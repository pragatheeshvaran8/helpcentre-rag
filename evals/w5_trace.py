"""Week 5: what one complete trace is, how it is captured, and how it is graded.

WHAT A TRACE HAS TO CONTAIN
    A trace is complete when someone else can replay the answer months later
    without asking you a single question. That means three groups of fields:

    1. The exact input.      The question, and the pool id it came from.
    2. The exact machinery.  Every setting that could change the output:
                             chunker, index, embedding model, retrieval mode,
                             k, gate threshold, RRF and BM25 constants, the LLM
                             name, temperature, reply cap, a hash of the prompt,
                             and a hash of the corpus.
    3. The exact output.     Every retrieved chunk with its rank and per-arm
                             ranks, the context string that was really sent,
                             the raw answer text, every citation and whether it
                             resolves, and whether the model or the gate refused.

    Two of those are easy to leave out and both are the ones that hurt. Without
    the prompt hash and the corpus hash, "I cannot reproduce it" has no answer,
    because the two things most likely to have drifted are invisible. Without
    the context string, you cannot tell a retrieval failure from a reading
    failure, which is the whole point of the exercise.

GRADING IS MECHANICAL AND CARRIES NO CATEGORIES
    This file decides only pass or fail, by the rule below. It never names a
    problem type. Naming problem types before reading the traces is how you end
    up finding the problems you expected instead of the ones you have.

    expected_behaviour = "answer"
        retrieval_ok  every requirement is met by some chunk in the top-k
        answer_ok     the model did not refuse, AND every requirement is met by
                      some chunk the answer actually cited and that resolves
        outcome       pass when retrieval_ok and answer_ok, otherwise fail

    expected_behaviour = "refuse"
        retrieval_ok  not applicable, recorded as None
        answer_ok     the app refused, by the gate or by the model
        outcome       pass when it refused, otherwise fail

    Requiring EVERY requirement is deliberate. A two-part question answered
    halfway is a wrong answer once it reaches a customer, so it is a fail here.
"""
from __future__ import annotations

import hashlib
import time
from datetime import datetime, timezone
from pathlib import Path

from config import STRATEGY_STRUCTURED, get_settings
from evals.w5_questions import ANSWER, REFUSE, W5_K
from rag.answerer import SYSTEM_PROMPT, USER_TEMPLATE, answer_question
from rag.retriever import chunk_answers_question, format_context, format_hits

# Bump when the shape of a trace changes, so an old results file is never
# silently mixed with a new one.
TRACE_SCHEMA_VERSION = "w5.1"

PASS = "pass"
FAIL = "fail"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def corpus_fingerprint() -> str:
    """One short hash over every corpus file, in name order.

    If this changes between two runs, the two runs are not comparable, however
    similar the numbers look.
    """
    settings = get_settings()
    digest = hashlib.sha256()
    for path in sorted(Path(settings.corpus_dir).glob("*.md")):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def prompt_fingerprint() -> str:
    """One short hash over the generation prompt, system and user template."""
    return _sha256(SYSTEM_PROMPT + "\n---\n" + USER_TEMPLATE)


def trace_config(strategy: str, mode: str, k: int) -> dict:
    """Every setting that could move an answer, captured with the trace.

    Copied by value rather than referenced, because config.py will keep
    changing and a trace has to stay true to the run that produced it.
    """
    s = get_settings()
    from rag.vector_store import count_chunks

    return {
        "strategy": strategy,
        "collection": {"baseline": "hc_baseline", "structured": "hc_structured"}[strategy],
        "retrieval_mode": mode,
        "k": k,
        "product_area_filter": None,
        "score_threshold": s.score_threshold,
        "embedding_model": s.embedding_model,
        "distance_metric": s.distance_metric,
        "chunk_size": s.chunk_size,
        "chunk_overlap": s.chunk_overlap,
        "chunk_count": count_chunks(strategy),
        "rrf_k": s.rrf_k,
        "bm25_k1": s.bm25_k1,
        "bm25_b": s.bm25_b,
        "llm_model": s.openrouter_model,
        "llm_temperature": s.llm_temperature,
        "llm_max_tokens": s.max_tokens,
        "prompt_sha": prompt_fingerprint(),
        "corpus_sha": corpus_fingerprint(),
    }


def _requirement_status(requirements: list[dict], hits: list[dict], citations: list) -> list[dict]:
    """For each requirement, which chunks met it in retrieval and in the answer.

    This is the field that makes a failure readable at a glance. When a
    requirement has an empty ``retrieved_by`` the model never saw that half of
    the answer. When ``retrieved_by`` is full and ``cited_by`` is empty, it saw
    it and did not use it. Those are different problems with different fixes.
    """
    out = []
    for req in requirements:
        retrieved_by = [
            h["chunk_id"]
            for h in hits
            if h["article_id"] == req["article_id"]
            and chunk_answers_question(h["text"], req["must_contain"])
        ]
        cited_by = [
            c.chunk_id
            for c in citations
            if c.resolves
            and c.article_id == req["article_id"]
            and c.text
            and chunk_answers_question(c.text, req["must_contain"])
        ]
        out.append(
            {
                "article_id": req["article_id"],
                "must_contain": req["must_contain"],
                "retrieved_by": retrieved_by,
                "cited_by": cited_by,
            }
        )
    return out


def grade(question: dict, hits: list[dict], citations: list, refused: bool) -> dict:
    """Pass or fail, by the rule in this module's docstring. No categories."""
    status = _requirement_status(question["requirements"], hits, citations)

    if question["expected_behaviour"] == REFUSE:
        return {
            "expected_behaviour": REFUSE,
            "retrieval_ok": None,
            "answer_ok": bool(refused),
            "outcome": PASS if refused else FAIL,
            "requirement_status": status,
        }

    retrieval_ok = all(r["retrieved_by"] for r in status)
    answer_ok = (not refused) and all(r["cited_by"] for r in status)
    return {
        "expected_behaviour": ANSWER,
        "retrieval_ok": retrieval_ok,
        "answer_ok": answer_ok,
        "outcome": PASS if (retrieval_ok and answer_ok) else FAIL,
        "requirement_status": status,
    }


def _retrieval_only(question_text: str, strategy: str, mode: str, k: int) -> tuple[list[dict], str]:
    """Retrieve without generating, so a dead API still leaves a usable trace."""
    from rag.hybrid import search_by_mode

    scored = search_by_mode(question_text, strategy, mode=mode, k=k, product_area=None)
    return format_hits(scored), format_context(scored)


def run_trace(
    question: dict,
    trace_id: str,
    draw_index: int,
    *,
    strategy: str = STRATEGY_STRUCTURED,
    mode: str | None = None,
    k: int = W5_K,
) -> dict:
    """Run one question end to end and return the complete trace record.

    A generation failure is recorded, never raised. Twenty paid calls is enough
    that losing the whole run to the nineteenth is a real risk, and a trace with
    an error field is honestly different from a trace with a refusal.
    """
    settings = get_settings()
    mode = mode or settings.retrieval_mode

    started = datetime.now(timezone.utc)
    t0 = time.perf_counter()
    error: str | None = None
    rerun_retrieval = False

    try:
        ans = answer_question(
            question["question"], strategy, k=k, mode=mode, use_gate=True
        )
        elapsed_ms = round((time.perf_counter() - t0) * 1000)
        hits = ans.retrieved
        context = ans.context
        raw_answer = ans.answer
        refused = ans.refused
        gate_fired = ans.gate_fired
        degraded = ans.budget_degraded
        citations = ans.citations
    except Exception as exc:  # noqa: BLE001 - recorded, not swallowed
        elapsed_ms = round((time.perf_counter() - t0) * 1000)
        error = f"{type(exc).__name__}: {exc}"
        # Retrieval costs nothing and is the half that is still knowable, so
        # capture it rather than leaving a hole in the trace.
        hits, context = _retrieval_only(question["question"], strategy, mode, k)
        rerun_retrieval = True
        raw_answer = ""
        refused = False
        gate_fired = False
        degraded = False
        citations = []

    trace = {
        "schema_version": TRACE_SCHEMA_VERSION,
        "trace_id": trace_id,
        "question_id": question["id"],
        "draw_index": draw_index,
        "kind": question["kind"],
        "question": question["question"],
        "expected_behaviour": question["expected_behaviour"],
        "requirements": question["requirements"],
        "started_at": started.isoformat(),
        "elapsed_ms": elapsed_ms,
        "config": trace_config(strategy, mode, k),
        "retrieval": {
            "rerun_after_generation_error": rerun_retrieval,
            "hits": hits,
        },
        "context_sent": context,
        "generation": {
            "raw_answer": raw_answer,
            "refused": refused,
            "gate_fired": gate_fired,
            "budget_degraded": degraded,
            "error": error,
        },
        "citations": [
            {
                "chunk_id": c.chunk_id,
                "resolves": c.resolves,
                "was_in_context": c.was_in_context,
                "article_id": c.article_id,
            }
            for c in citations
        ],
        "replay": (
            f"python -m evals.w5_collect --only {question['id']} --force"
        ),
    }

    if error is None:
        trace["grading"] = grade(question, hits, citations, refused)
    else:
        # An unanswered question has no honest grade. Marking it a failure would
        # inflate the failure count with the provider's problem, not the app's.
        trace["grading"] = {
            "expected_behaviour": question["expected_behaviour"],
            "retrieval_ok": None,
            "answer_ok": None,
            "outcome": "error",
            "requirement_status": _requirement_status(question["requirements"], hits, []),
        }

    return trace


REQUIRED_TOP_LEVEL = (
    "schema_version", "trace_id", "question_id", "draw_index", "kind", "question",
    "expected_behaviour", "requirements", "started_at", "elapsed_ms", "config",
    "retrieval", "context_sent", "generation", "citations", "grading", "replay",
)

REQUIRED_CONFIG = (
    "strategy", "collection", "retrieval_mode", "k", "score_threshold",
    "embedding_model", "chunk_count", "rrf_k", "bm25_k1", "bm25_b",
    "llm_model", "llm_temperature", "llm_max_tokens", "prompt_sha", "corpus_sha",
)


def missing_fields(trace: dict) -> list[str]:
    """Which required fields a trace is missing. Empty means complete."""
    gaps = [f for f in REQUIRED_TOP_LEVEL if f not in trace]
    config = trace.get("config", {})
    gaps += [f"config.{f}" for f in REQUIRED_CONFIG if f not in config]
    if not trace.get("retrieval", {}).get("hits"):
        gaps.append("retrieval.hits")
    return gaps
