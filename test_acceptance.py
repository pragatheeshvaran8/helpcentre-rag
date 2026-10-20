"""Acceptance tests. Checks every claim the write-up makes.

    python test_acceptance.py                    retrieval only, no API key
    python test_acceptance.py --with-generation  also test citations and refusals

Exits non-zero if anything fails, so it works in CI.

These are assertions about behaviour, not a unit-test suite. Each one maps to a
sentence in results/results.md that a grader could challenge.
"""
from __future__ import annotations

import argparse
import sys

from config import BASE_DIR, STRATEGIES, STRATEGY_STRUCTURED, get_settings
from rag import term

REQUIRED_METADATA = ("source_file", "article_id", "product_area", "last_updated", "chunk_id")

passed = 0
failed = 0


def check(label: str, ok: bool, detail: str = "") -> bool:
    """Record one result and print it."""
    global passed, failed
    if ok:
        passed += 1
        print(f"{term.green('PASS')}  {label}" + (f"  {term.grey(detail)}" if detail else ""))
    else:
        failed += 1
        print(f"{term.paint('FAIL', 'red', 'bold')}  {label}" + (f"  {term.red(detail)}" if detail else ""))
    return ok


def info(label: str, detail: str) -> None:
    print(f"{term.cyan('INFO')}  {label}  {term.grey(detail)}")


# ---------------------------------------------------------------------------
def test_corpus() -> None:
    from rag.documents import load_corpus

    articles = load_corpus()
    check("corpus loads", len(articles) == 6, f"{len(articles)} articles")

    missing = [
        a.source_file
        for a in articles
        if not all([a.article_id, a.title, a.product_area, a.last_updated])
    ]
    check("every article has full front matter", not missing, str(missing))

    ids = sorted(a.article_id for a in articles)
    check("article ids are unique", len(set(ids)) == len(ids), ", ".join(ids))


def test_index() -> None:
    from rag.vector_store import count_chunks

    counts = {s: count_chunks(s) for s in STRATEGIES}
    check(
        "both indexes are built",
        all(counts.values()),
        ", ".join(f"{s}={n}" for s, n in counts.items()),
    )
    if not all(counts.values()):
        print(term.red("\n  Index is empty. Run:  python -m rag.ingest\n"))
        raise SystemExit(1)


def test_metadata() -> None:
    from rag.vector_store import get_store

    for strategy in STRATEGIES:
        got = get_store(strategy)._collection.get(include=["metadatas"])
        bad = [
            cid
            for cid, md in zip(got["ids"], got["metadatas"])
            if any(not md.get(f) for f in REQUIRED_METADATA)
        ]
        check(f"{strategy}: every chunk has full metadata", not bad, f"{len(bad)} bad")

        mismatched = [
            cid for cid, md in zip(got["ids"], got["metadatas"]) if md.get("chunk_id") != cid
        ]
        check(f"{strategy}: chunk_id matches the primary key", not mismatched)


def test_structure_guarantee() -> None:
    """The one hard promise: a table row never loses its header row."""
    from rag.vector_store import get_store

    orphans = {}
    for strategy in STRATEGIES:
        got = get_store(strategy)._collection.get(include=["metadatas"])
        orphans[strategy] = [
            cid for cid, md in zip(got["ids"], got["metadatas"]) if md.get("orphan_table_rows")
        ]

    check(
        "structure-aware: NO chunk has table rows without a header",
        not orphans[STRATEGY_STRUCTURED],
        f"{len(orphans[STRATEGY_STRUCTURED])} orphans",
    )
    info(
        "baseline, for contrast",
        f"{len(orphans['baseline'])} header-less chunks: {', '.join(orphans['baseline'])}",
    )


def test_resolvable_citations() -> None:
    from rag.vector_store import get_chunk_by_id, get_store

    for strategy in STRATEGIES:
        ids = get_store(strategy)._collection.get(include=[])["ids"]
        unresolved = [cid for cid in ids if get_chunk_by_id(strategy, cid) is None]
        check(
            f"{strategy}: every chunk_id resolves back out of the store",
            not unresolved,
            f"{len(ids)} ids checked",
        )

    check(
        "a made-up chunk_id does NOT resolve",
        get_chunk_by_id(STRATEGY_STRUCTURED, "HC-9999-structured-999") is None,
    )


def test_hit_rate() -> None:
    from evals.questions import QUESTIONS
    from evals.run_search_eval import evaluate_question

    k = get_settings().top_k
    for strategy in STRATEGIES:
        results = [evaluate_question(q, strategy, k) for q in QUESTIONS]
        hits = sum(1 for r in results if r["hit"])
        misses = [r["question_id"] for r in results if not r["hit"]]
        check(
            f"{strategy}: all 8 known-answer questions hit in top-{k}",
            hits == len(QUESTIONS),
            f"{hits}/{len(QUESTIONS)}" + (f", missed {misses}" if misses else ""),
        )


def test_metadata_filter() -> None:
    from evals.questions import FILTER_DEMO
    from rag.retriever import format_hits, search

    query, value = FILTER_DEMO["query"], FILTER_DEMO["filter_value"]
    unfiltered = format_hits(search(query, STRATEGY_STRUCTURED))
    filtered = format_hits(search(query, STRATEGY_STRUCTURED, product_area=value))

    check("filtered search returns results", bool(filtered), f"{len(filtered)} hits")
    check(
        f"every filtered result is product_area={value}",
        all(h["product_area"] == value for h in filtered),
    )
    check(
        "the filter changes top-1",
        unfiltered[0]["chunk_id"] != filtered[0]["chunk_id"],
        f"{unfiltered[0]['chunk_id']} -> {filtered[0]['chunk_id']}",
    )
    promoted = {h["chunk_id"] for h in filtered} - {h["chunk_id"] for h in unfiltered}
    check(
        "it is a pre-filter, not a post-filter",
        bool(promoted),
        f"{len(promoted)} chunk(s) promoted from outside the unfiltered top-5",
    )


def test_generation() -> None:
    """Needs an API key. Costs 6 LLM calls."""
    from evals.questions import ANSWERABLE, OUT_OF_CORPUS, get_question
    from rag.answerer import answer_question

    for qid in ANSWERABLE:
        q = get_question(qid)
        ans = answer_question(q["question"], STRATEGY_STRUCTURED, use_gate=True)
        check(f"{qid}: answered, not refused", not ans.refused)
        check(f"{qid}: produced at least one citation", bool(ans.citations))
        check(
            f"{qid}: every citation resolves",
            ans.all_citations_resolve,
            ", ".join(c.chunk_id for c in ans.citations),
        )
        check(
            f"{qid}: cited chunk really contains the answer",
            any(
                c.text and all(m.lower() in c.text.lower() for m in q["must_contain"])
                for c in ans.citations
            ),
            "must_contain: " + ", ".join(q["must_contain"]),
        )

    for item in OUT_OF_CORPUS:
        ans = answer_question(item["question"], STRATEGY_STRUCTURED, use_gate=False)
        best = ans.retrieved[0]["score"] if ans.retrieved else 0.0
        check(
            f"{item['id']}: refused an out-of-corpus question",
            ans.refused,
            f"top score {best:.4f}, gate_fired={ans.gate_fired}",
        )
        check(
            f"{item['id']}: the MODEL refused, not the gate",
            ans.refused and not ans.gate_fired,
        )



# ---------------------------------------------------------------------------
# Week 4
# ---------------------------------------------------------------------------
def test_keyword_arm() -> None:
    """The BM25 arm must keep a code as one token, or it cannot help."""
    from rag.keyword import build_index, search_keyword, tokenize
    from rag.vector_store import get_chunk_by_id, get_store

    tokens = tokenize("What does ERR-7208 mean?")
    check(
        "tokeniser keeps err-7208 as one token",
        "err-7208" in tokens,
        str(tokens),
    )
    check(
        "tokeniser also emits the parts",
        "err" in tokens and "7208" in tokens,
    )

    index = build_index(STRATEGY_STRUCTURED)
    check(
        "BM25 index covers every chunk",
        len(index) == len(get_store(STRATEGY_STRUCTURED)._collection.get(include=[])["ids"]),
        f"{len(index)} chunks",
    )
    check(
        "a rare code has a higher IDF than a common word",
        index.idf.get("err-7208", 0) > index.idf.get("the", 99),
        f"err-7208={index.idf.get('err-7208', 0):.3f} the={index.idf.get('the', 0):.3f}",
    )

    top = search_keyword("ERR-7208", STRATEGY_STRUCTURED, k=1)
    ok = bool(top) and "ERR-7208" in (get_chunk_by_id(STRATEGY_STRUCTURED, top[0][0]) or {}).get("text", "")
    check(
        "BM25 alone ranks the ERR-7208 chunk first",
        ok,
        top[0][0] if top else "nothing returned",
    )


def test_one_change_only() -> None:
    """Hybrid must differ from dense in retrieval only, nothing else."""
    from config import get_settings
    from rag.hybrid import search_hybrid
    from rag.retriever import search as search_dense

    settings = get_settings()
    check(
        "both modes share one embedding model",
        settings.embedding_model == "BAAI/bge-small-en-v1.5",
        settings.embedding_model,
    )
    check(
        "RRF constant left at the conventional value",
        settings.rrf_k == 60,
        f"rrf_k={settings.rrf_k}",
    )
    check(
        "BM25 parameters left at standard defaults",
        (settings.bm25_k1, settings.bm25_b) == (1.5, 0.75),
        f"k1={settings.bm25_k1} b={settings.bm25_b}",
    )

    q = "A customer sees ERR-4032 on their invoice. What is the cause and the fix?"
    dense_ids = {d.metadata["chunk_id"] for d, _ in search_dense(q, STRATEGY_STRUCTURED, k=20)}
    hybrid_ids = {d.metadata["chunk_id"] for d, _ in search_hybrid(q, STRATEGY_STRUCTURED, k=5)}
    check(
        "hybrid draws from the same chunk universe, it does not re-chunk",
        hybrid_ids <= dense_ids | set(build_index_ids()),
        f"{len(hybrid_ids)} fused ids",
    )


def build_index_ids() -> list:
    from rag.keyword import build_index

    return build_index(STRATEGY_STRUCTURED).ids


def test_hybrid_improves_hit_rate() -> None:
    """The headline claim: hybrid beats dense at k=3, and breaks nothing."""
    from evals.w4_measure import evaluate
    from evals.w4_questions import W4_K, W4_QUESTIONS

    before, after, regressions = 0, 0, []
    for q in W4_QUESTIONS:
        d = evaluate(q, "dense", STRATEGY_STRUCTURED)
        h = evaluate(q, "hybrid", STRATEGY_STRUCTURED)
        before += int(d["hit_at_k"])
        after += int(h["hit_at_k"])
        if d["hit_at_k"] and not h["hit_at_k"]:
            regressions.append(q["id"])

    n = len(W4_QUESTIONS)
    check(
        f"hybrid hit-rate@{W4_K} is at least dense",
        after >= before,
        f"{before}/{n} -> {after}/{n}",
    )
    check(
        f"hybrid strictly improves hit-rate@{W4_K}",
        after > before,
        f"+{after - before}",
    )
    check(
        "hybrid breaks nothing dense already found",
        not regressions,
        f"regressions: {regressions}" if regressions else "none",
    )


def test_w4_question_set() -> None:
    """The Week 4 set must be answerable from the corpus, and unrigged."""
    import pathlib

    from evals.w4_questions import W4_QUESTIONS

    corpus = " ".join(
        p.read_text(encoding="utf-8") for p in pathlib.Path("corpus").glob("*.md")
    ).lower()
    missing = [
        (q["id"], m)
        for q in W4_QUESTIONS
        for m in q["must_contain"]
        if m.lower() not in corpus
    ]
    check("every W4 answer string is verbatim in the corpus", not missing, str(missing[:3]))
    check(
        "one question per code, no duplicates",
        len({q["code"] for q in W4_QUESTIONS}) == len(W4_QUESTIONS),
        f"{len(W4_QUESTIONS)} questions",
    )


# ---------------------------------------------------------------------------
def test_w5_pool() -> None:
    """The Week 5 traffic pool. A broken question would invent a fake failure."""
    from pathlib import Path

    from config import STRATEGY_STRUCTURED
    from evals.w5_questions import ANSWER, REFUSE, W5_POOL
    from rag.retriever import chunk_answers_question
    from rag.vector_store import get_store

    ids = [q["id"] for q in W5_POOL]
    check("w5 pool has 60 questions", len(W5_POOL) == 60, f"{len(W5_POOL)}")
    check("w5 pool ids are unique", len(set(ids)) == len(ids))

    corpus_dir = Path(get_settings().corpus_dir)
    articles = {
        "-".join(path.name.split("-")[:2]): path.read_text(encoding="utf-8").lower()
        for path in corpus_dir.glob("*.md")
    }
    missing = [
        (q["id"], needle)
        for q in W5_POOL
        for req in q["requirements"]
        for needle in req["must_contain"]
        if needle.lower() not in articles.get(req["article_id"], "")
    ]
    check(
        "every w5 required string is verbatim in its article",
        not missing,
        str(missing[:3]),
    )

    data = get_store(STRATEGY_STRUCTURED).get(include=["documents", "metadatas"])
    chunks = list(zip(data["documents"], data["metadatas"]))
    unsatisfiable = [
        (q["id"], req["article_id"])
        for q in W5_POOL
        for req in q["requirements"]
        if not any(
            md.get("article_id") == req["article_id"]
            and chunk_answers_question(text, req["must_contain"])
            for text, md in chunks
        )
    ]
    check(
        "every w5 requirement is satisfiable by one chunk",
        not unsatisfiable,
        str(unsatisfiable[:3]),
    )

    shapes_wrong = [
        q["id"]
        for q in W5_POOL
        if (q["expected_behaviour"] == ANSWER) != bool(q["requirements"])
    ]
    check(
        "answerable questions carry requirements, refusals carry none",
        not shapes_wrong,
        str(shapes_wrong[:3]),
    )
    check(
        "only two expected behaviours exist",
        {q["expected_behaviour"] for q in W5_POOL} == {ANSWER, REFUSE},
    )


# ---------------------------------------------------------------------------
def test_w5_sample_is_not_curated() -> None:
    """The 20 traces that were read were drawn, not chosen."""
    import random

    from evals.w5_questions import W5_POOL
    from evals.w5_sample import W5_SAMPLE_SIZE, W5_SEED, draw_ids

    first, second = draw_ids(), draw_ids()
    check("the draw is reproducible", first == second)

    expected = random.Random(W5_SEED).sample([q["id"] for q in W5_POOL], W5_SAMPLE_SIZE)
    check("the draw is plain random.sample over the pool in file order", first == expected)
    check("the draw is 20 distinct questions", len(set(first)) == 20, f"{len(first)}")
    check("every drawn id is in the pool", set(first) <= {q["id"] for q in W5_POOL})

    # A different seed must give a different sample. If it does not, the draw is
    # not really random and the fairness claim is empty.
    check("a different seed gives a different sample", draw_ids(seed=W5_SEED + 1) != first)


# ---------------------------------------------------------------------------
def test_w5_traces_are_complete() -> None:
    """A trace has to be replayable and re-gradable from the record alone."""
    import json
    from pathlib import Path

    from evals.w5_sample import draw_ids
    from evals.w5_trace import (
        corpus_fingerprint,
        grade,
        missing_fields,
        prompt_fingerprint,
    )
    from rag.vector_store import get_chunk_by_id

    path = Path(get_settings().results_dir) / "w5_traces.json"
    if not path.exists():
        check("w5 traces exist", False, "run python -m evals.w5_collect")
        return
    traces = json.loads(path.read_text(encoding="utf-8"))

    check("20 traces were collected", len(traces) == 20, f"{len(traces)}")
    check(
        "the traces are the drawn sample, in draw order",
        [t["question_id"] for t in traces] == draw_ids(),
    )
    check(
        "no trace was left in the error state",
        not [t["trace_id"] for t in traces if t["grading"]["outcome"] == "error"],
    )

    gaps = [(t["trace_id"], missing_fields(t)) for t in traces]
    gaps = [g for g in gaps if g[1]]
    check("every trace carries every required field", not gaps, str(gaps[:2]))

    # A trace is stale when it can no longer be reproduced, not when the project
    # has moved on. These twenty were captured under prompt v1. Week 6 made v2
    # active, so the original check went red and stayed red for six weeks while
    # nothing was actually wrong: v1 is still in the file and the corpus has not
    # changed, so every one of them still replays.
    #
    # Two things genuinely break a trace, and both are checked:
    #   the corpus moved   -> its chunk ids may no longer resolve
    #   its prompt is gone -> it cannot be reproduced at all
    from evals.w5_trace import known_prompt_fingerprints

    known = set(known_prompt_fingerprints().values())

    moved_corpus = [
        t["trace_id"] for t in traces if t["config"]["corpus_sha"] != corpus_fingerprint()
    ]
    check(
        "no trace was taken against a different corpus",
        not moved_corpus,
        str(moved_corpus[:3]),
    )

    lost_prompt = [t["trace_id"] for t in traces if t["config"]["prompt_sha"] not in known]
    check(
        "every trace's prompt is still in the codebase, so it can be replayed",
        not lost_prompt,
        str(lost_prompt[:3]),
    )

    on_current = sum(1 for t in traces if t["config"]["prompt_sha"] == prompt_fingerprint())
    info(
        "w5 traces vs the active prompt",
        f"{on_current}/{len(traces)} on the current prompt; the rest are v1 records "
        "and replay against v1",
    )

    unresolvable = [
        (t["trace_id"], hit["chunk_id"])
        for t in traces
        for hit in t["retrieval"]["hits"]
        if get_chunk_by_id(t["config"]["strategy"], hit["chunk_id"]) is None
    ]
    check(
        "every retrieved chunk_id still resolves, so a trace can be replayed",
        not unresolvable,
        str(unresolvable[:2]),
    )

    # Re-grade each trace from what the file holds. If the stored grade cannot be
    # rebuilt, the trace is not self-contained however complete it looks.
    class _Cite:
        def __init__(self, record: dict, strategy: str) -> None:
            resolved = get_chunk_by_id(strategy, record["chunk_id"]) or {}
            self.chunk_id = record["chunk_id"]
            self.resolves = record["resolves"]
            self.article_id = record["article_id"]
            self.text = resolved.get("text")

    disagreements = []
    for t in traces:
        rebuilt = grade(
            {
                "expected_behaviour": t["expected_behaviour"],
                "requirements": t["requirements"],
            },
            t["retrieval"]["hits"],
            [_Cite(c, t["config"]["strategy"]) for c in t["citations"]],
            t["generation"]["refused"],
        )
        if rebuilt["outcome"] != t["grading"]["outcome"]:
            disagreements.append(
                (t["trace_id"], t["grading"]["outcome"], rebuilt["outcome"])
            )
    check(
        "every stored grade can be rebuilt from the trace alone",
        not disagreements,
        str(disagreements[:3]),
    )


# ---------------------------------------------------------------------------
def test_w5_notes_came_before_the_groups() -> None:
    """The open coding must not quote a category that did not exist yet."""
    import json
    from pathlib import Path

    from evals.w5_notes import NOTES
    from evals.w5_taxonomy import GROUPS

    path = Path(get_settings().results_dir) / "w5_traces.json"
    if not path.exists():
        check("w5 traces exist", False, "run python -m evals.w5_collect")
        return
    trace_ids = [t["trace_id"] for t in json.loads(path.read_text(encoding="utf-8"))]

    check(
        "every trace has a hand-written note, including the ones that passed",
        sorted(NOTES) == sorted(trace_ids),
        f"{len(NOTES)} notes for {len(trace_ids)} traces",
    )
    check("no note is empty", all(note.strip() for note in NOTES.values()))

    note_text = " ".join(NOTES.values()).lower()
    leaked = [g["name"] for g in GROUPS if g["name"].lower() in note_text]
    check(
        "no note names a group, so the notes were not written backwards",
        not leaked,
        str(leaked),
    )


# ---------------------------------------------------------------------------
def test_w5_taxonomy_and_prediction() -> None:
    """The groups must agree with the traces, and the prediction must be falsifiable."""
    from evals.w5_taxonomy import (
        GROUPS,
        PREDICTION,
        SEVERITY_SCALE,
        TARGET_KEY,
        assigned_trace_ids,
        consistency_problems,
        failing_trace_ids,
        ranking,
        target,
    )

    problems = consistency_problems()
    check("the taxonomy agrees with the traces", not problems, "; ".join(problems))

    assigned = assigned_trace_ids()
    check(
        "every failing trace is in exactly one group",
        sorted(assigned) == sorted(failing_trace_ids()),
        f"{len(assigned)} assigned",
    )
    check("no group is empty", all(g["traces"] for g in GROUPS))
    check(
        "every severity is on the written scale",
        all(g["severity"] in SEVERITY_SCALE for g in GROUPS),
    )
    check(
        "every group name is a phrase a stranger could read",
        all(len(g["name"].split()) >= 4 for g in GROUPS),
        str([g["name"] for g in GROUPS if len(g["name"].split()) < 4]),
    )

    ranked = ranking()
    scores = [g["score"] for g in ranked]
    check(
        "the ranking is sorted by frequency times severity",
        scores == sorted(scores, reverse=True),
    )
    check(
        "every score really is frequency times severity",
        all(g["score"] == g["frequency"] * g["severity"] for g in ranked),
    )

    chosen = target()
    check("exactly one target is chosen", chosen["key"] == TARGET_KEY, chosen["name"])
    check(
        "the target is one of the top-scoring groups",
        chosen["score"] == ranked[0]["score"],
        f"{chosen['score']} vs {ranked[0]['score']}",
    )

    check("the prediction names the change", bool(PREDICTION["change"].strip()))
    check("the prediction has metrics", len(PREDICTION["metrics"]) >= 2)
    incomplete = [
        m["metric"]
        for m in PREDICTION["metrics"]
        if not (m.get("now") and m.get("predicted") and m.get("falsified_if"))
    ]
    check("every predicted metric says what would falsify it", not incomplete, str(incomplete))
    check(
        "the prediction is measured on more than the traces it came from",
        "60" in PREDICTION["measured_on"] or "pool" in PREDICTION["measured_on"],
    )
    check("the prediction carries a guard against a cheap win", bool(PREDICTION["guard"].strip()))




# ---------------------------------------------------------------------------
# Week 7: the agent, its stop conditions, and the race
# ---------------------------------------------------------------------------
def test_w7_tickets() -> None:
    """The ticket set has to contain the case AGAINST an agent, not just for it."""
    from evals.w7_tickets import MULTI, REFUSE, SINGLE, TICKETS, counts, ticket_set
    from rag.keyword import build_index
    from rag.retriever import chunk_answers_question

    n = counts()
    check(
        "every ticket shape is represented",
        all(n[s] > 0 for s in (MULTI, SINGLE, REFUSE)),
        str(n),
    )
    check(
        "there are single-part tickets, so the loop can lose",
        n[SINGLE] >= 3,
        f"{n[SINGLE]} single-part",
    )
    check(
        "there are tickets the corpus cannot answer",
        n[REFUSE] >= 2,
        f"{n[REFUSE]} out of corpus",
    )

    ids = [t["id"] for t in TICKETS]
    check("ticket ids are unique", len(ids) == len(set(ids)))

    multi = [t for t in TICKETS if t["shape"] == MULTI]
    check(
        "every multi-part ticket really has several parts",
        all(len(t["requirements"]) >= 2 for t in multi),
        str([t["id"] for t in multi if len(t["requirements"]) < 2]),
    )
    check(
        "the parts count matches the requirements",
        all(t["parts"] == max(len(t["requirements"]), 1) for t in TICKETS),
        str([t["id"] for t in TICKETS if t["parts"] != max(len(t["requirements"]), 1)]),
    )

    narrow = [t["id"] for t in multi if len({r["article_id"] for r in t["requirements"]}) < 2]
    check(
        "most multi-part tickets span more than one article",
        len(narrow) <= 1,
        f"single-article: {narrow}",
    )

    # A requirement no chunk can satisfy is a ticket nobody can ever pass.
    index = build_index(STRATEGY_STRUCTURED)
    unsatisfiable = []
    for ticket in TICKETS:
        for req in ticket["requirements"]:
            if not any(
                index.metadatas[i].get("article_id") == req["article_id"]
                and chunk_answers_question(index.texts[i], req["must_contain"])
                for i in range(len(index.ids))
            ):
                unsatisfiable.append((ticket["id"], req["article_id"]))
    check("every requirement is satisfiable by a real chunk", not unsatisfiable, str(unsatisfiable))

    check(
        "ticket_set carries the kind key the checks read",
        all("kind" in t for t in ticket_set()),
    )


def test_w7_tools() -> None:
    """A tool must never raise, and the descriptions must tell them apart."""
    from agent.tools import TOOLS, catalogue, execute

    check("there is a terminal tool", "finish" in TOOLS)
    check("there is more than one way to look something up", len(TOOLS) >= 3, str(list(TOOLS)))

    for name, tool in TOOLS.items():
        check(f"{name} has a description a model could act on", len(tool.description) > 80)

    check(
        "each search tool says what the other is for",
        "lookup_error_code" in TOOLS["search_help_centre"].description
        and "search_help_centre" in TOOLS["lookup_error_code"].description,
    )
    text = catalogue()
    check("the catalogue names every tool", all(name in text for name in TOOLS))

    # Every failure path returns an observation instead of raising.
    failures = [
        ("unknown tool", "nope", {}),
        ("wrong argument", "search_help_centre", {"wrong": 1}),
        ("not a code", "lookup_error_code", {"code": "how do I void an invoice"}),
        ("empty query", "search_help_centre", {"query": ""}),
    ]
    for label, name, args in failures:
        try:
            result = execute(name, args)
            check(f"{label} comes back as an observation, not an exception", not result.ok)
        except Exception as exc:
            check(f"{label} comes back as an observation, not an exception", False, str(exc))

    exact = execute("lookup_error_code", {"code": "ERR-4032"})
    check("an exact code lookup finds the code", exact.ok and bool(exact.chunks))
    sloppy = execute("lookup_error_code", {"code": "err 4032"})
    check(
        "a sloppily typed code finds the same chunk",
        bool(sloppy.chunks)
        and bool(exact.chunks)
        and sloppy.chunks[0]["chunk_id"] == exact.chunks[0]["chunk_id"],
    )


def local_toolbox():
    """The in-process tools, so loop tests do not start MCP subprocesses."""
    from agent.tools import local_toolbox as _box

    return _box()


def _scripted(loop_mod, *replies):
    """A stand-in for the model, so the loop can be tested without an API key."""
    it = iter(replies)

    # *_ on purpose. _decide has gained a parameter in three separate weeks
    # (guarded, toolbox, meter) and each time this stub broke a dozen checks
    # with a TypeError that looked like a loop bug. The first three arguments
    # are what the stub actually uses; anything the loop adds after them is
    # the loop's business, not the stub's.
    def fake(ticket, memory, budget, *_, **__):
        budget.spend_call()
        raw = next(it, '{"thought":"","tool":"finish","args":{"answer":"stub"}}')
        try:
            return loop_mod._parse(raw), raw
        except Exception:
            return None, raw

    return fake


def test_w7_stop_conditions() -> None:
    """A loop without a proven exit is exactly what this week warns about."""
    import json as _json

    import agent.loop as loop_mod
    from agent.budget import CALL_LIMIT, FINISHED, REPEAT_LIMIT, STEP_LIMIT, Budget

    real_decide, real_forced = loop_mod._decide, loop_mod._forced_answer
    try:
        loop_mod._forced_answer = lambda t, m, b, *_: "REFUSED: stub, the budget ran out."

        loop_mod._decide = _scripted(
            loop_mod,
            '{"thought":"a","tool":"lookup_error_code","args":{"code":"ERR-4032"}}',
            '{"thought":"b","tool":"finish","args":{"answer":"Re-map it [HC-4002-structured-004]."}}',
        )
        done = loop_mod.run("ERR-4032?", toolbox=local_toolbox(), log_trace=False)
        check("a loop that calls finish stops with finished", done.stop_reason == FINISHED)
        check("a finished run records every step", len(done.steps) == 2)
        check("a finished run resolves its citations", any(c.resolves for c in done.citations))
        check("a finished run keeps what the tools returned", len(done.retrieved) > 0)

        endless = [
            _json.dumps(
                {"thought": f"t{i}", "tool": "search_help_centre", "args": {"query": f"q{i}"}}
            )
            for i in range(50)
        ]

        loop_mod._decide = _scripted(loop_mod, *endless)
        capped = loop_mod.run("never ends", budget=Budget(max_steps=3), toolbox=local_toolbox(), log_trace=False)
        check("the step limit stops the loop", capped.stop_reason == STEP_LIMIT)
        check("the step limit is obeyed exactly", len(capped.steps) == 3, str(len(capped.steps)))

        loop_mod._decide = _scripted(loop_mod, *endless)
        broke = loop_mod.run("never ends", budget=Budget(max_steps=99, max_llm_calls=4), toolbox=local_toolbox(), log_trace=False)
        check("the call limit stops the loop", broke.stop_reason == CALL_LIMIT)

        # A repeat is warned once, then stopped. The first live run repeated at
        # the exact moment it had every fact it needed, and stopping there threw
        # away a complete run. One warning usually converts that into a finish.
        loop_mod._decide = _scripted(
            loop_mod,
            '{"thought":"a","tool":"search_help_centre","args":{"query":"vat"}}',
            '{"thought":"a","tool":"search_help_centre","args":{"query":"vat"}}',
            '{"thought":"fine","tool":"finish","args":{"answer":"ok [HC-4002-structured-004]"}}',
        )
        warned = loop_mod.run("repeats once, then takes the hint", toolbox=local_toolbox(), log_trace=False)
        check(
            "the first repeat is a warning, not a stop",
            warned.stop_reason == FINISHED,
            warned.stop_reason,
        )
        check(
            "the warning is recorded as its own step",
            any(s.tool == "(repeated)" for s in warned.steps),
            str([s.tool for s in warned.steps]),
        )

        loop_mod._decide = _scripted(
            loop_mod,
            '{"thought":"a","tool":"search_help_centre","args":{"query":"vat"}}',
            '{"thought":"a","tool":"search_help_centre","args":{"query":"vat"}}',
            '{"thought":"a","tool":"search_help_centre","args":{"query":"vat"}}',
        )
        stuck = loop_mod.run("going nowhere", toolbox=local_toolbox(), log_trace=False)
        check(
            "a repeat after the warning does stop the loop",
            stuck.stop_reason == REPEAT_LIMIT,
            stuck.stop_reason,
        )

        loop_mod._decide = _scripted(loop_mod, *endless)
        cut = loop_mod.run("never ends", budget=Budget(max_steps=2), toolbox=local_toolbox(), log_trace=False)
        check("a cut-short run still produces an answer", bool(cut.answer))
        check("a cut-short run is never labelled complete", not cut.completed)

        loop_mod._decide = _scripted(
            loop_mod,
            "I will search the help centre now.",
            '{"thought":"ok","tool":"finish","args":{"answer":"done [HC-4002-structured-004]"}}',
        )
        recovered = loop_mod.run("bad json first", toolbox=local_toolbox(), log_trace=False)
        check("an unparsable reply costs a step, not the run", recovered.stop_reason == FINISHED)
        check("the unparsable step is recorded", recovered.steps[0].tool == "(unparsed)")
    finally:
        loop_mod._decide, loop_mod._forced_answer = real_decide, real_forced


def test_w7_parser() -> None:
    """The protocol has to survive what a weak model actually emits."""
    from agent.loop import _parse

    survivable = {
        "a raw newline, which every refusal has": (
            '{"thought":"x","tool":"finish","args":{"answer":"REFUSED: not here.\n'
            'Missing: that topic."}}'
        ),
        "a code fence": '```json\n{"thought":"x","tool":"finish","args":{"answer":"d"}}\n```',
        "chatter around the object": (
            'Sure:\n{"thought":"x","tool":"search_help_centre","args":{"query":"vat"}}\nHope that helps'
        ),
    }
    for label, raw in survivable.items():
        try:
            check(f"the parser survives {label}", bool(_parse(raw)["tool"]))
        except Exception as exc:
            check(f"the parser survives {label}", False, f"{type(exc).__name__}: {exc}")

    for label, raw in {
        "prose with no object": "I think I should search next.",
        "an object with no tool": '{"thought":"x"}',
    }.items():
        try:
            _parse(raw)
            check(f"the parser rejects {label}", False, "it was accepted")
        except Exception:
            check(f"the parser rejects {label}", True)


def test_w7_race_is_fair() -> None:
    """Both runners must be scored by the same rules, or the race proves nothing."""
    from agent.loop import AgentRun
    from agent.workflow import WorkflowRun
    from evals.w7_race import part_coverage, recommend
    from evals.w7_tickets import TICKETS_BY_ID

    for field_name in ("answer", "refused", "retrieved", "citations", "elapsed_s", "llm_calls"):
        check(
            f"both runners expose {field_name} to the scorer",
            hasattr(AgentRun(question="x"), field_name)
            and hasattr(WorkflowRun(question="x"), field_name),
        )

    ticket = TICKETS_BY_ID["T01"]

    class _Cite:
        def __init__(self, article_id, text):
            self.chunk_id = "c"
            self.article_id = article_id
            self.text = text
            self.resolves = True

    class _Run:
        def __init__(self, retrieved, citations):
            self.retrieved = retrieved
            self.citations = citations

    hits = [
        {"article_id": "HC-4002", "text": "ERR-4032 fix: Billing then Tax Codes"},
        {"article_id": "HC-4005", "text": "ERR-7215 fix: update the legal entity name"},
    ]
    cites = [_Cite(h["article_id"], h["text"]) for h in hits]

    full = part_coverage(_Run(hits, cites), ticket)
    check("a fully answered two-part ticket scores 2 of 2", full.cited == 2 and full.fully_cited)

    partial = part_coverage(_Run(hits[:1], cites[:1]), ticket)
    check("a half answered two-part ticket scores 1 of 2", partial.cited == 1)
    check("a half answered ticket is not counted as fully answered", not partial.fully_cited)

    # The recommendation must be derivable, and must be able to say "workflow".
    agent_better = {
        "multi_fully_cited": 5,
        "multi_n": 6,
        "calls_per_ticket": 3.0,
        "median_seconds": 9.0,
        "by_shape": {"single": {"passed": 4, "llm_calls": 12}, "refuse": {"passed": 2}},
    }
    workflow_row = {
        "multi_fully_cited": 2,
        "multi_n": 6,
        "calls_per_ticket": 1.0,
        "median_seconds": 3.0,
        "by_shape": {"single": {"passed": 4, "llm_calls": 4}, "refuse": {"passed": 2}},
    }
    check("the rule can pick the agent", recommend(agent_better, workflow_row).ship == "agent")
    check(
        "the rule picks the simple one when the loop buys no coverage",
        recommend(dict(agent_better, multi_fully_cited=2), workflow_row).ship == "workflow",
    )
    check(
        "the rule picks the simple one when the loop is worse",
        recommend(dict(agent_better, multi_fully_cited=1), workflow_row).ship == "workflow",
    )
    check(
        "the recommendation always carries a reason",
        bool(recommend(agent_better, workflow_row).reason),
    )




# ---------------------------------------------------------------------------
# Week 8: trajectory, injection, and the one fix
# ---------------------------------------------------------------------------
def test_w8_trajectory_finds_the_gap() -> None:
    """Outcome-only scoring must be shown to miss something real."""
    import json
    from pathlib import Path

    from evals.run_race import _Replayed
    from evals.w7_race import score
    from evals.w7_tickets import ticket_set
    from evals.w8_trajectory import LOOPED, QUIET_GIVE_UP, evaluate, summarise

    path = Path(get_settings().results_dir) / "w7_race" / "agent__runs.json"
    if not path.exists():
        check("w7 agent runs exist to score", False, "run the Week 7 race first")
        return
    runs = json.loads(path.read_text(encoding="utf-8"))

    trajs = []
    for ticket in ticket_set():
        record = runs.get(ticket["id"])
        if record is None:
            continue
        run = _Replayed(record)
        trajs.append(evaluate(ticket, run, score(ticket, run).passed))

    s = summarise(trajs)
    check("every Week 7 ticket has a trajectory", s["n"] == 12, str(s["n"]))
    check(
        "outcome-only scoring reports a clean sweep",
        s["outcome_passed"] == s["n"],
        f"{s['outcome_passed']}/{s['n']}",
    )
    check(
        "the trajectory layer disagrees with it",
        s["trajectory_clean"] < s["outcome_passed"],
        f"clean {s['trajectory_clean']} vs passed {s['outcome_passed']}",
    )
    check("there is at least one right-answer-wrong-path case", s["gap"] >= 1, str(s["gap_ids"]))
    check("looping is one of the modes found", LOOPED in s["modes"], str(s["modes"]))
    check(
        "the quiet give-up is caught",
        QUIET_GIVE_UP in s["modes"],
        "an error string shaped like a refusal must not score as a refusal",
    )
    check("cost per task is reported", s["calls_mean"] > 0 and s["calls_p99"] > 0)
    check(
        "p99 is labelled as the worst run, not a real percentile",
        s.get("calls_p99_is_max") is True,
    )


def test_w8_quiet_give_up() -> None:
    """A crash dressed as a refusal is the failure outcome checks cannot see."""
    from evals.w8_trajectory import looks_like_quiet_give_up

    give_ups = {
        "the real one from T11": (
            "REFUSED: The help-centre corpus does not contain this information.\n"
            "Missing: the run stopped early (RateLimitError)."
        ),
        "budget exhaustion": (
            "REFUSED: The help-centre corpus does not contain this information.\n"
            "Missing: nothing was retrieved before the run hit its limit."
        ),
    }
    for label, text in give_ups.items():
        check(f"quiet give-up caught: {label}", looks_like_quiet_give_up(text))

    real = {
        "a genuine refusal": (
            "REFUSED: The help-centre corpus does not contain this information.\n"
            "Missing: SLA targets for a P1 billing incident."
        ),
        "a normal answer": "Re-map the line item [HC-4002-structured-004].",
    }
    for label, text in real.items():
        check(f"not flagged: {label}", not looks_like_quiet_give_up(text))


def test_w8_loop_detection() -> None:
    """The threshold must separate real loops from healthy runs, with margin."""
    import itertools
    import json
    from pathlib import Path

    from agent.budget import SIMILARITY, similar_query

    path = Path(get_settings().results_dir) / "w7_race" / "agent__runs.json"
    if not path.exists():
        check("w7 agent runs exist for the threshold check", False)
        return
    runs = json.loads(path.read_text(encoding="utf-8"))

    def queries(tid):
        return [
            (s.get("args") or {}).get("query") or (s.get("args") or {}).get("code") or ""
            for s in runs[tid]["steps"]
            if s["tool"] in ("search_help_centre", "lookup_error_code")
        ]

    looping = ("T11", "T12")
    healthy = ("T01", "T02", "T03", "T04", "T05", "T06", "T07", "T08", "T09", "T10")

    caught = sum(
        1
        for tid in looping
        for a, b in itertools.combinations(queries(tid), 2)
        if similar_query(a, b)
    )
    check("the known looping runs are caught", caught >= 8, f"{caught} loop pairs")

    false_positives = [
        (tid, a, b)
        for tid in healthy
        for a, b in itertools.combinations(queries(tid), 2)
        if similar_query(a, b)
    ]
    check(
        "no healthy run is called a loop",
        not false_positives,
        str(false_positives[:2]),
    )

    # The threshold was chosen from data. Assert the margin still exists, so a
    # later edit to the corpus or the tickets cannot quietly close it.
    import re as _re

    def jac(a, b):
        wa = set(_re.findall(r"[a-z0-9]+", a.lower()))
        wb = set(_re.findall(r"[a-z0-9]+", b.lower()))
        return len(wa & wb) / len(wa | wb) if wa and wb else 0.0

    healthy_max = max(
        (jac(a, b) for tid in healthy for a, b in itertools.combinations(queries(tid), 2)),
        default=0.0,
    )
    check(
        "the threshold sits above every healthy pair",
        healthy_max < SIMILARITY,
        f"healthy max {healthy_max:.2f} vs threshold {SIMILARITY}",
    )


def test_w8_loop_guard_stops_a_loop() -> None:
    """The guard must stop a rewording agent. Driven by a scripted model."""
    import json as _json

    import agent.loop as loop_mod
    from agent.budget import REPEAT_LIMIT, Budget

    real_decide, real_forced = loop_mod._decide, loop_mod._forced_answer
    reworded = [
        _json.dumps({"thought": "t", "tool": "search_help_centre", "args": {"query": q}})
        for q in (
            "P1 billing incident SLA",
            "P1 incident SLA response time",
            "P1 incident SLA",
            "SLA response time",
            "P1 incident SLA response time",
        )
    ]
    try:
        loop_mod._forced_answer = lambda t, m, b, *_: "REFUSED: stub."

        loop_mod._decide = _scripted(loop_mod, *reworded)
        guarded_run = loop_mod.run("SLA?", budget=Budget(similar_guard=True), toolbox=local_toolbox(), log_trace=False)
        check(
            "the loop guard stops an agent that rewords the same search",
            guarded_run.stop_reason == REPEAT_LIMIT,
            guarded_run.stop_reason,
        )

        loop_mod._decide = _scripted(loop_mod, *reworded)
        old_run = loop_mod.run("SLA?", budget=Budget(similar_guard=False, max_steps=6), toolbox=local_toolbox(), log_trace=False)
        check(
            "the Week 7 guard alone does NOT stop it",
            old_run.stop_reason != REPEAT_LIMIT,
            old_run.stop_reason,
        )
        check(
            "the fix costs fewer steps than the old guard",
            len(guarded_run.steps) < len(old_run.steps),
            f"{len(guarded_run.steps)} vs {len(old_run.steps)}",
        )
    finally:
        loop_mod._decide, loop_mod._forced_answer = real_decide, real_forced


def test_w8_injection_scanner() -> None:
    """Every payload must be caught, and no real text may be."""
    from agent.guard import scan
    from evals.w7_tickets import TICKETS
    from evals.w8_injection import ATTACKS

    for attack in ATTACKS:
        result = scan(attack.payload)
        check(
            f"{attack.id} payload is stripped ({attack.kind}, {attack.goal})",
            not result.clean,
            str(result.hits),
        )

    corpus_lines = [
        "| ERR-4032 | References a legacy tax code. | Re-map under Billing then Tax Codes. |",
        "Never void an invoice that a customer has already paid, even if it shows an error code.",
        "There is no extension process, and customers who ask should be routed to their manager.",
        "A webhook delivery that does not return a 2xx within 10 seconds is treated as failed.",
    ]
    bad = [line for line in corpus_lines if not scan(line).clean]
    check("real corpus text is not redacted", not bad, str(bad[:1]))

    flagged = [t["id"] for t in TICKETS if not scan(t["question"]).clean]
    check("real tickets are not redacted", not flagged, str(flagged))


def test_w8_output_validation() -> None:
    """The last layer checks what came out, whatever produced it."""
    from agent.guard import validate_output
    from evals.w8_injection import MARKER

    blocked = {
        "an attack marker": f"Here you go: {MARKER}",
        "a leaked system prompt": "My rules: You work in a loop. Each turn you write one thought.",
    }
    for label, text in blocked.items():
        verdict = validate_output(text, markers=(MARKER,))
        check(f"output blocked: {label}", not verdict.allowed, str(verdict.reasons))
        check(
            f"a blocked output is replaced with a refusal: {label}",
            verdict.answer.upper().startswith("REFUSED"),
        )

    allowed = {
        "a cited answer": "Re-map the line item [HC-4002-structured-004].",
        "a genuine refusal": (
            "REFUSED: The help-centre corpus does not contain this information.\n"
            "Missing: SLA targets."
        ),
    }
    for label, text in allowed.items():
        check(f"output allowed: {label}", validate_output(text, markers=(MARKER,)).allowed)


def test_w8_least_privilege() -> None:
    """The blast radius is set by what the tools can reach, not by the filters."""
    import inspect

    from agent import tools

    # Match real use, not prose. The first version grepped raw substrings and
    # tripped on the word "subprocesses" inside a docstring.
    source = chr(10).join(
        line
        for line in inspect.getsource(tools).splitlines()
        if not line.lstrip().startswith("#")
    )
    forbidden = {
        "shell execution": ("import subprocess", "os.system(", ".popen("),
        "file writing": ("open(", ".write(", "shutil."),
        "outbound network": ("requests.", "httpx.", "urllib.request"),
        # Named precisely. A bare "token" matched a local variable holding the
        # normalised error code, which is not a credential.
        "credentials": ("api_key", "apikey", "secret", "password", "bearer ", "credential"),
    }
    for label, needles in forbidden.items():
        hits = [n for n in needles if n in source]
        check(f"tool functions cannot reach: {label}", not hits, str(hits))

    check(
        "every tool is declared in one registry",
        set(tools.TOOLS) == {"search_help_centre", "lookup_error_code", "finish"},
        str(sorted(tools.TOOLS)),
    )


def test_w8_defence_is_measured_not_assumed() -> None:
    """A defended attack must be stopped by a layer, not by the model's mood."""
    import json
    from pathlib import Path

    base = Path(get_settings().results_dir) / "w8_runs"
    undefended = base / "attacks_undefended.json"
    defended = base / "attacks_defended.json"
    if not (undefended.exists() and defended.exists()):
        info("w8 attack runs", "not run yet, skipping the measured check")
        return

    u = json.loads(undefended.read_text(encoding="utf-8"))
    d = json.loads(defended.read_text(encoding="utf-8"))

    landed_undefended = [k for k, v in u.items() if v["attack_landed"]]
    check(
        "at least one attack lands without defences",
        landed_undefended,
        f"landed: {landed_undefended}",
    )

    still_landing = [k for k, v in d.items() if v["attack_landed"]]
    check("no attack lands with defences on", not still_landing, str(still_landing))

    # The important one. An attack that "failed" with no layer firing proves
    # nothing: the model simply chose not to comply that run.
    unexplained = [
        k
        for k, v in d.items()
        if k in landed_undefended and not v["injection_hits"] and not v["output_blocked"]
    ]
    check(
        "every blocked attack was blocked by a layer, not by luck",
        not unexplained,
        f"nothing fired on: {unexplained}",
    )




# ---------------------------------------------------------------------------
# Week 9: MCP, discovery, and the server bolted on without touching the agent
# ---------------------------------------------------------------------------
def test_w9_handshake() -> None:
    """The protocol, end to end, against a real server process."""
    from agent.mcp_client import PROTOCOL_VERSION, MCPClient, python_server

    try:
        with MCPClient(
            "ticket-history", python_server("mcp_servers.ticket_history_server")
        ) as client:
            check("the server completes the handshake", bool(client.protocol_version))
            check(
                "the server names itself",
                client.server_info.get("name") == "ticket-history",
                str(client.server_info),
            )
            check(
                "client and server agree on a protocol version",
                client.protocol_version == PROTOCOL_VERSION,
                f"{client.protocol_version} vs {PROTOCOL_VERSION}",
            )

            tools = client.list_tools()
            check("tools/list returns tools", len(tools) == 2, str([t.name for t in tools]))
            check(
                "every tool arrives with a schema",
                all(t.schema.get("properties") for t in tools),
            )
            check(
                "every tool arrives with a description the model can act on",
                all(len(t.description) > 60 for t in tools),
            )

            text = client.call_tool("find_similar_tickets", {"error_code": "ERR-4032"})
            check("tools/call returns text", "SUP-2041" in text, text[:60])

            log = client.transcript(4)
            methods = [e["msg"].get("method") for e in log if e["dir"] == "->"]
            check(
                "the handshake is initialize then notifications/initialized",
                methods[:2] == ["initialize", "notifications/initialized"],
                str(methods[:3]),
            )
    except Exception as exc:
        check("the MCP handshake works", False, f"{type(exc).__name__}: {exc}")


def test_w9_discovery_not_hardcoding() -> None:
    """The agent must not know a tool's name until a server tells it."""
    import inspect

    import agent.loop as loop_mod
    from agent.toolbox import connect, load_config

    servers = load_config()
    check("mcp_servers.json lists servers", len(servers) >= 2, str([s["name"] for s in servers]))
    check(
        "every configured server declares whether it is trusted",
        all("trusted" in s for s in servers),
        str([s["name"] for s in servers if "trusted" not in s]),
    )

    # The real proof of decoupling: the loop cannot name a tool.
    source = inspect.getsource(loop_mod)
    remote_names = ("search_help_centre", "lookup_error_code", "get_ticket_history",
                    "find_similar_tickets")
    leaked = [n for n in remote_names if n in source]
    check(
        "agent/loop.py names no discovered tool",
        not leaked,
        f"leaked: {leaked}",
    )
    check(
        "agent/loop.py still owns finish, because that is its own control flow",
        'action["tool"] == "finish"' in source or "FINISH" in source,
    )

    try:
        with connect(servers) as box:
            check("every configured server started", not box.servers_down, str(box.servers_down))
            check(
                "tools were discovered from more than one server",
                len({t.server for t in box.tools.values()} - {"local"}) >= 2,
                str({t.server for t in box.tools.values()}),
            )
            check(
                "finish is local and was never discovered",
                box.tools["finish"].server == "local",
            )
            check(
                "the catalogue says which server each tool came from",
                all(s in box.catalogue() for s in box.servers_up),
            )
    except Exception as exc:
        check("discovery works", False, f"{type(exc).__name__}: {exc}")


def test_w9_bolt_on_without_touching_the_agent() -> None:
    """The Week 9 deliverable, asserted rather than claimed."""
    import hashlib
    from pathlib import Path

    from agent.toolbox import connect, load_config

    def agent_hashes() -> dict:
        return {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted((BASE_DIR / "agent").glob("*.py"))
        }

    before = agent_hashes()
    full = load_config()
    without = [s for s in full if s["name"] != "ticket-history"]
    check("the bolt-on server is in the config", len(without) == len(full) - 1)

    try:
        with connect(without) as box:
            minus = set(box.names())
        with connect(full) as box:
            plus = set(box.names())
    except Exception as exc:
        check("both configurations connect", False, f"{type(exc).__name__}: {exc}")
        return

    gained = plus - minus
    check(
        "adding the server to config adds its tools",
        gained == {"get_ticket_history", "find_similar_tickets"},
        str(sorted(gained)),
    )
    check("removing it takes them away again", not (gained & minus), str(sorted(gained & minus)))

    after = agent_hashes()
    changed = [k for k in before if before[k] != after.get(k)]
    check(
        "no agent source file changed between the two configurations",
        not changed,
        f"changed: {changed}",
    )


def test_w9_recoverable_errors() -> None:
    """A broken server must cost its own tools and nothing else."""
    from agent.toolbox import connect, load_config

    broken = {
        "name": "does-not-exist",
        "command": ["python", "-m", "mcp_servers.no_such_module"],
        "trusted": False,
    }
    servers = load_config() + [broken]
    try:
        with connect(servers) as box:
            check(
                "a server that will not start is recorded, not raised",
                any(name == "does-not-exist" for name, _ in box.servers_down),
                str(box.servers_down),
            )
            check(
                "the working servers still came up",
                "helpcentre" in box.servers_up and "ticket-history" in box.servers_up,
                str(box.servers_up),
            )
            result = box.execute("no_such_tool", {})
            check("an unknown tool comes back as an observation", not result.ok)
            check("the observation lists what IS available", "finish" in result.observation)
    except Exception as exc:
        check("a broken server does not take the agent down", False, f"{type(exc).__name__}: {exc}")


def test_w9_tool_poisoning() -> None:
    """A tool description is prompt text, so an untrusted one must be scanned."""
    from agent import guard
    from agent.toolbox import connect
    from mcp_servers.hostile_server import CLEAN_DESCRIPTION, POISONED_DESCRIPTION

    check(
        "the hostile description really does carry an injection",
        not guard.scan(POISONED_DESCRIPTION).clean,
        str(guard.scan(POISONED_DESCRIPTION).hits),
    )
    check(
        "its harmless first line is not what trips the scanner",
        guard.scan(CLEAN_DESCRIPTION).clean,
    )

    hostile = {
        "name": "ticket-archive",
        "command": ["python", "-m", "mcp_servers.hostile_server"],
        "trusted": False,
    }
    try:
        with connect([hostile]) as box:
            desc = next(t.description for t in box.tools.values() if t.server == "ticket-archive")
            check(
                "an untrusted server's description is scanned before the model sees it",
                guard.REDACTION in desc,
                desc[:70],
            )
            check("what was stripped is recorded", bool(box.poisoned), str(box.poisoned))
            check(
                "the harmless part of the description survives",
                "archived tickets" in desc.lower(),
            )

        with connect([dict(hostile, trusted=True)]) as box:
            desc = next(t.description for t in box.tools.values() if t.server == "ticket-archive")
            check(
                "a trusted server is NOT scanned, which is what the flag costs",
                guard.REDACTION not in desc,
            )
    except Exception as exc:
        check("the poisoning demo runs", False, f"{type(exc).__name__}: {exc}")


def test_w9_privilege_boundary_moved() -> None:
    """Week 9 changed the security posture. Say where the new line is.

    Week 8 asserted that nothing in the tool layer could reach a shell. That is
    still true of the tool FUNCTIONS, and it is no longer true of the agent as
    a whole: agent/mcp_client.py starts server processes, because that is what
    a stdio transport is.

    So the boundary moved. It is no longer "no subprocess". It is "only the
    commands an operator wrote in mcp_servers.json". This asserts that, rather
    than leaving the Week 8 claim standing when it has stopped being complete.
    """
    import inspect
    import json

    from agent import mcp_client, toolbox

    check(
        "the client really does start processes, so the Week 8 claim narrowed",
        "subprocess.Popen" in inspect.getsource(mcp_client),
    )

    source = inspect.getsource(toolbox)
    check(
        "the only commands ever run come from the config file",
        "server[\"command\"]" in source,
        "commands must not be built from tool output or model output",
    )

    config = json.loads((BASE_DIR / "mcp_servers.json").read_text(encoding="utf-8"))
    commands = [s["command"] for s in config.get("servers", [])]
    check("every configured command is a fixed list, not a string", all(isinstance(c, list) for c in commands))
    check(
        "no configured command goes through a shell",
        not any(any(tok in " ".join(c) for tok in ("|", ";", "&&", ">")) for c in commands),
        str(commands),
    )
    check(
        "the agent never builds a server command from model output",
        "shell=True" not in inspect.getsource(mcp_client),
    )


def test_w9_chunk_ids_survive_the_wire() -> None:
    """MCP returns text, so anything the scorers need must be recoverable from it."""
    from agent.toolbox import _chunks_from

    text = (
        "Help-centre entry for ERR-4032:\n\n[HC-4002-structured-004] (article HC-4002)\n"
        "| ERR-4032 | Legacy tax code. | Re-map under Billing then Tax Codes. |"
    )
    chunks = _chunks_from(text)
    check("a chunk id in the text resolves to a real chunk", len(chunks) == 1, str(len(chunks)))
    if chunks:
        check(
            "the resolved chunk carries the article id the checks read",
            chunks[0]["article_id"] == "HC-4002",
            str(chunks[0].get("article_id")),
        )
        check(
            "the resolved chunk carries the body text the checks read",
            "Tax Codes" in chunks[0]["text"],
        )
    check("an invented chunk id resolves to nothing", not _chunks_from("[HC-9999-structured-001]"))
    check("text with no chunk ids yields no chunks", not _chunks_from("no ids here"))




# ---------------------------------------------------------------------------
# Week 10: the squad, and whether the race between it and the single agent
# is actually fair
# ---------------------------------------------------------------------------
def test_w10_race_is_fair() -> None:
    """The mentor's first question. Both sides must run the SAME tests."""
    import inspect

    from evals import run_w10
    from evals.w7_tickets import TICKETS

    source = inspect.getsource(run_w10)

    check(
        "both runners are raced over one ticket list",
        "ticket_set()" in source and "w7_tickets" in source,
    )
    check(
        "the ticket set is the Week 7 one, unchanged",
        len(TICKETS) == 12,
        f"{len(TICKETS)} tickets",
    )
    check(
        "one MCP toolbox is built and handed to both",
        source.count("connect(") == 1 and "toolbox=box" in source,
        "a second toolbox would charge one side for a start-up the other avoided",
    )
    check(
        "both are scored by the same quality scorer",
        "from evals.w7_race import part_coverage, score" in source,
    )
    check(
        "both are scored by the same trajectory scorer",
        "from evals.w8_trajectory import evaluate" in source,
    )
    check(
        "all four required numbers are summarised",
        all(k in source for k in ("pass_rate", "median_seconds", "total_tokens", "priced_cost")),
    )


def test_w10_meter_uses_the_provider_numbers() -> None:
    """Tokens must come from the provider, not from a guess on our side."""
    from agent.meter import USD_PER_MILLION_INPUT, USD_PER_MILLION_OUTPUT, Meter

    class Reply:
        usage_metadata = {"input_tokens": 100, "output_tokens": 25, "total_tokens": 125}
        response_metadata = {"token_usage": {"cost": 0.0}}

    meter = Meter()
    meter.record("agent", "step 1", Reply())
    meter.record("manager", "split", Reply())

    check("the meter reads the provider's input tokens", meter.input_tokens == 200)
    check("the meter reads the provider's output tokens", meter.output_tokens == 50)
    check("totals add up", meter.total_tokens == 250)
    check("calls are counted", meter.n_calls == 2)
    check(
        "a free model reports zero cost, and that is recorded honestly",
        meter.reported_cost == 0.0,
    )

    expected = 200 / 1_000_000 * USD_PER_MILLION_INPUT + 50 / 1_000_000 * USD_PER_MILLION_OUTPUT
    check(
        "the priced estimate is arithmetic on the real token counts",
        abs(meter.priced_cost - expected) < 1e-12,
    )

    by_who = meter.by_who()
    check(
        "tokens are attributed per participant",
        set(by_who) == {"agent", "manager"},
        str(sorted(by_who)),
    )
    check(
        "per-participant input tokens are tracked, which is where a hand-off shows",
        by_who["manager"]["input_tokens"] == 100,
    )

    # A reply with no usage block must not silently count as zero-cost truth.
    class Bare:
        usage_metadata = None
        response_metadata = {}

    bare = Meter()
    bare.record("agent", "step 1", Bare())
    check("a reply with no usage report records a call", bare.n_calls == 1)
    check("and does not invent token counts", bare.total_tokens == 0)


def test_w10_agent_cards_route() -> None:
    """The manager must route by card, not by a hard-coded name."""
    import inspect

    from agent import squad

    check("there is a manager plus two specialists", len(squad.SQUAD) == 2,
          str([c.name for c in squad.SQUAD]))

    for card in squad.SQUAD:
        check(f"{card.name} publishes what it is for", len(card.description) > 50)
        check(f"{card.name} publishes skills to route on", len(card.skills) >= 3)
        check(f"{card.name} declares which tools it may use", bool(card.tools))

    overlap = set(squad.CODE_DESK.tools) & set(squad.POLICY_DESK.tools)
    check(
        "the specialists do not share tools, so the split is real",
        not overlap,
        str(overlap),
    )

    # The routing proof: the manager's prompt is built from cards, and its code
    # does not name a specialist.
    check(
        "the manager prompt is built from the cards",
        "{cards}" in squad.MANAGER_SPLIT,
    )
    run_source = inspect.getsource(squad.run)
    named = [c.name for c in squad.SQUAD if f'"{c.name}"' in run_source]
    check(
        "the manager's code names no specialist",
        not named,
        f"named: {named}",
    )
    check(
        "routing is a lookup in the card registry",
        "CARDS.get(assignee)" in run_source,
    )


def test_w10_task_lifecycle() -> None:
    """Every hand-off is a task with a state, and a failure stays local."""
    from agent.squad import COMPLETED, FAILED, SUBMITTED, WORKING, Task

    check(
        "the four A2A states exist",
        {SUBMITTED, WORKING, COMPLETED, FAILED} == {"submitted", "working", "completed", "failed"},
    )

    task = Task(task_id="t1", assignee="code_desk", instruction="look up ERR-4032")
    check("a new task starts as submitted", task.state == SUBMITTED)

    task.state = FAILED
    task.error = "boom"
    row = task.as_dict()
    check("a failed task records why", row["error"] == "boom" and row["state"] == FAILED)
    check("a task records who it went to", row["assignee"] == "code_desk")
    check("a task records what was asked", "ERR-4032" in row["instruction"])


def test_w10_specialists_are_narrow() -> None:
    """A specialist that could do everything is just the single agent."""
    import inspect

    from agent import squad

    source = inspect.getsource(squad._run_specialist)
    check(
        "a specialist is offered only its own tools plus finish",
        "card.tools" in source and '"finish"' in source,
    )
    check(
        "reaching for another specialist's tool is refused, not executed",
        "that tool is not yours" in source,
    )
    check(
        "a specialist has its own small step budget",
        squad.SPECIALIST_MAX_STEPS <= 4,
        str(squad.SPECIALIST_MAX_STEPS),
    )
    check(
        "a specialist failure fails its task, not the run",
        "task.state = FAILED" in source,
    )
    check(
        "the manager is told to give one specialist one question",
        "Never give one specialist two questions" in squad.MANAGER_SPLIT,
    )
    check(
        "the manager may only use what its specialists reported",
        "Use ONLY what your specialists reported" in squad.MANAGER_ASSEMBLE,
    )


def test_w10_verdict_rule() -> None:
    """The verdict must be derivable, and must be able to say 'keep the single'."""
    from evals.run_w10 import SINGLE, SQUAD, verdict

    cheap_single = {"passed": 10, "parts_cited_rate": 0.95, "total_tokens": 30_000}
    dear_squad = {"passed": 10, "parts_cited_rate": 0.95, "total_tokens": 90_000}

    tie = verdict(cheap_single, dear_squad)
    check(
        "on a quality tie the cheaper side wins",
        tie["keep"] == SINGLE,
        tie["keep"],
    )
    check("the token ratio is reported", tie["token_ratio"] == 3.0, str(tie["token_ratio"]))
    check("the verdict carries a reason", len(tie["why"]) > 60)

    better_squad = dict(dear_squad, passed=12)
    won = verdict(cheap_single, better_squad)
    check(
        "the rule CAN pick the squad when it answers more tickets",
        won["keep"] == SQUAD,
        won["keep"],
    )

    worse_squad = dict(dear_squad, passed=7)
    lost = verdict(cheap_single, worse_squad)
    check("a worse and dearer squad loses", lost["keep"] == SINGLE)

    one_ticket = dict(dear_squad, passed=11)
    check(
        "a one-ticket gap is treated as a real gap, not noise",
        verdict(cheap_single, one_ticket)["keep"] == SQUAD,
        "the rule says one whole ticket is the threshold",
    )


def test_w10_context_resend_is_measurable() -> None:
    """The week's central claim has to be checkable from the records."""
    import json
    from pathlib import Path

    base = Path(get_settings().results_dir) / "w10_runs"
    squad_path = base / "squad__runs.json"
    if not squad_path.exists():
        info("w10 squad runs", "not run yet, skipping the measured check")
        return

    runs = json.loads(squad_path.read_text(encoding="utf-8"))
    if not runs:
        info("w10 squad runs", "cache is empty, skipping")
        return

    with_who = [r for r in runs.values() if (r.get("meter") or {}).get("by_who")]
    check(
        "every squad run attributes its tokens per participant",
        len(with_who) == len(runs),
        f"{len(with_who)}/{len(runs)}",
    )

    sample = next(iter(runs.values()))
    who = sample["meter"]["by_who"]
    check(
        "the manager's tokens are recorded separately from the specialists'",
        "manager" in who,
        str(sorted(who)),
    )
    check(
        "a ticket costs more than one call once it is split",
        sample["meter"]["calls"] >= 2,
        str(sample["meter"]["calls"]),
    )
    check(
        "input tokens are recorded, which is where a hand-off shows its cost",
        sample["meter"]["input_tokens"] > 0,
    )




# ---------------------------------------------------------------------------
# Week 11: logging, the support drill, cost, and the failure-to-test loop
# ---------------------------------------------------------------------------
def test_w11_trace_shape() -> None:
    """A trace has to carry enough to find a request AND to replay it."""
    from obs.trace import Trace, current_config, new_trace_id, replay_config

    a, b = new_trace_id(), new_trace_id()
    check("trace ids are unique", a != b)
    check("a trace id is short enough to read down a phone", len(a) <= 16, f"{len(a)} chars")

    t = Trace(question="ERR-4032?", config=current_config("agent"))
    s1 = t.span("agent:step 1")
    s1.close(ms=120.0, input_tokens=900, output_tokens=40, cost=0.0004)
    s2 = t.span("tool:lookup_error_code")
    s2.close(ms=15.0, detail="1 chunk")

    row = t.as_dict()
    for field_name in ("trace_id", "at", "question", "answer", "chunk_ids",
                       "citations", "spans", "config", "ms", "total_tokens", "cost"):
        check(f"a trace records {field_name}", field_name in row)

    check("spans are recorded per step", len(row["spans"]) == 2)
    check("a span carries its own ms", row["spans"][0]["ms"] == 120.0)
    check("a span carries its own tokens", row["spans"][0]["input_tokens"] == 900)
    check("a span carries its own cost", row["spans"][0]["cost"] == 0.0004)
    check(
        "a tool step is a span too, even with no tokens",
        row["spans"][1]["name"].startswith("tool:") and row["spans"][1]["ms"] == 15.0,
    )
    check("trace totals are the sum of its spans", row["total_tokens"] == 940)
    check(
        "a call with no tokens is not counted as an LLM call",
        row["llm_calls"] == 1,
        str(row["llm_calls"]),
    )

    for key in ("model", "prompt_sha", "corpus_sha", "strategy"):
        check(f"the config captures {key}, so the run can be reproduced", key in row["config"])

    same = replay_config(row)
    check("a trace taken now reproduces under today's settings", same["reproducible"])
    drifted = replay_config(dict(row, config=dict(row["config"], prompt_sha="old")))
    check(
        "a trace from an older prompt is reported as drifted, not reproducible",
        not drifted["reproducible"] and "prompt_sha" in drifted["drifted"],
    )


def test_w11_meter_emits_spans() -> None:
    """Cost per step must come from the same place as cost in total."""
    from agent.meter import Meter
    from obs.trace import Trace

    trace = Trace(question="x")
    meter = Meter()
    meter.trace = trace

    class Reply:
        usage_metadata = {"input_tokens": 300, "output_tokens": 50}
        response_metadata = {"token_usage": {"cost": 0.0}}

    meter.record("agent", "step 1", Reply(), 1.5)
    meter.record("agent", "step 2", Reply(), 0.5)

    check("every metered call becomes a span", len(trace.spans) == 2)
    check("the span carries the call's own time", trace.spans[0].ms == 1500.0)
    check(
        "trace tokens and meter tokens agree",
        trace.total_tokens == meter.total_tokens,
        f"{trace.total_tokens} vs {meter.total_tokens}",
    )
    check("a free model's zero cost is replaced by the priced estimate", trace.cost > 0)


def test_w11_log_and_search() -> None:
    """The log has to be searchable, and the drill has to find the needle."""
    from obs import plant, search, store

    rows = store.read_all()
    if not rows:
        info("w11 trace log", "not built yet, skipping")
        return

    check("the log holds traces", len(rows) >= 20, f"{len(rows)} traces")
    check("every trace has an id", all(r.get("trace_id") for r in rows))
    check("every trace has a timestamp", all(r.get("at") for r in rows))
    check("every trace has spans", all(r.get("spans") for r in rows))
    check(
        "some traces carry measured per-step tokens",
        any(any(s.get("input_tokens") for s in r["spans"]) for r in rows),
    )

    first = rows[0]["trace_id"]
    check("a trace can be fetched by id", store.by_id(first) is not None)
    check("an unknown id returns nothing rather than guessing", store.by_id("nope") is None)

    planted = [r for r in rows if (r.get("config") or {}).get("planted")]
    if not planted:
        info("w11 planted answer", "not planted yet, skipping the drill check")
        return
    check("exactly one bad answer is planted", len(planted) == 1, str(len(planted)))

    hits, report = search.search("refund card migration token", limit=5)
    check("the search returns in a few milliseconds", report["ms"] < 500, f"{report['ms']}ms")
    ids = [h.trace_id for h in hits]
    check(
        "the planted answer is in the top 5 for the complaint's words",
        planted[0]["trace_id"] in ids,
        str(ids[:3]),
    )
    check(
        "it ranks first",
        ids and ids[0] == planted[0]["trace_id"],
        f"top was {ids[0] if ids else 'nothing'}",
    )

    # The drill must be won by searching, not by reading the marker.
    import inspect
    source = inspect.getsource(search)
    check(
        "the search never filters on the planted marker",
        "planted" not in source,
        "finding the needle by its label would prove nothing",
    )


def test_w11_proof_step() -> None:
    """Finding it is not enough. You have to be able to show it is wrong."""
    from obs import plant, store

    rows = [r for r in store.read_all() if (r.get("config") or {}).get("planted")]
    if not rows:
        info("w11 planted answer", "not planted yet, skipping")
        return

    bad, why = plant.contradicts_its_citation(rows[0])
    check("the planted answer is proved wrong against its own citation", bad)
    check("the proof quotes the corpus line", plant.WHAT_THE_CORPUS_SAYS in why)
    check("the proof names the chunk", plant.CITED_CHUNK in why)

    correct = dict(
        rows[0],
        answer=(
            "The refund cannot go back to the card. It must be issued as "
            "account credit instead [HC-4003-structured-006]."
        ),
    )
    check("a correct answer is not flagged", not plant.contradicts_its_citation(correct)[0])

    unrelated = dict(
        rows[0],
        answer="Re-map the line item under Billing then Tax Codes [HC-4002-structured-004].",
        citations=["HC-4002-structured-004"],
    )
    check("an unrelated answer is not flagged", not plant.contradicts_its_citation(unrelated)[0])


def test_w11_cache_is_fenced() -> None:
    """A cached answer is only valid under the settings that produced it."""
    import tempfile
    from pathlib import Path

    from obs.cache import AnswerCache, codes_in, similarity

    cache = AnswerCache(path=Path(tempfile.mktemp(suffix=".json")))
    cache.clear()
    entry = cache.put(
        "Getting ERR-4032 on an invoice line. What is the fix?",
        answer="Re-map the line item under Billing then Tax Codes.",
        chunk_ids=[], citations=[], refused=False, trace_id="T07",
    )
    entry.fence = "fence-a"

    check("the same question hits exactly", cache.lookup(
        "Getting ERR-4032 on an invoice line. What is the fix?",
        now_fence="fence-a").kind == "exact")
    check(
        "a reworded question still hits",
        cache.lookup("hi, getting ERR-4032 on an invoice line. What is the fix?",
                     now_fence="fence-a").hit,
    )
    check(
        "a different fence empties the cache rather than serving stale answers",
        not cache.lookup("Getting ERR-4032 on an invoice line. What is the fix?",
                         now_fence="fence-b").hit,
    )

    # The dangerous near-miss, and the thing that stops it.
    near = "Getting ERR-4044 on an invoice line. What is the fix?"
    score = similarity(near, entry.question)
    check(
        "two questions differing only by error code score above the threshold",
        score >= cache.threshold,
        f"{score:.3f} vs threshold {cache.threshold}",
    )
    found = cache.lookup(near, now_fence="fence-a")
    check(
        "and are NOT served, because the codes differ",
        not found.hit,
        "this is the near-miss that would hand a customer the wrong fix",
    )
    check("the block is explained", "error code" in found.blocked_by, found.blocked_by)
    check(
        "codes are compared by identity, not as words",
        codes_in(near) != codes_in(entry.question),
    )


def test_w11_cost_improved_and_risk_measured() -> None:
    """A saving only counts if the wrong answers were counted too."""
    from obs import measure, store

    if not store.read_all():
        info("w11 trace log", "not built yet, skipping")
        return

    rep = measure.replay()
    d = rep.as_dict()
    check("the replay covers the whole log", d["requests"] >= 20, str(d["requests"]))
    check(
        "cost per request goes down",
        d["cost_per_request_after"] < d["cost_per_request_before"],
        f"{d['cost_per_request_before']:.8f} -> {d['cost_per_request_after']:.8f}",
    )
    check(
        "LLM calls go down",
        d["calls_after"] < d["calls_before"],
        f"{d['calls_before']} -> {d['calls_after']}",
    )
    check("the saving is reported as a rate", 0 < d["cost_saving"] < 1, str(d["cost_saving"]))

    risk = measure.risk()
    check(
        "the risk is measured, not assumed",
        risk.served > 0,
        "a risk check that serves nothing proves nothing",
    )
    check(
        "no cached answer is served for a different ticket",
        risk.wrong == 0,
        f"{risk.wrong} wrong of {risk.served} served: {risk.cases[:2]}",
    )


def test_w11_failure_became_a_test() -> None:
    """The loop closes only if the check fires on the real failing answer."""
    from evals.w11_regressions import REGRESSIONS

    check("at least one failure is pinned", len(REGRESSIONS) >= 1)

    for reg in REGRESSIONS:
        check(f"{reg.id} records where it was found", bool(reg.found_in_trace))
        check(f"{reg.id} records what went wrong", len(reg.what_went_wrong) > 80)
        check(f"{reg.id} keeps the answer that actually failed", bool(reg.failing_answer))

        ok_bad, reasons = reg.judge(reg.failing_answer)
        check(
            f"{reg.id} catches the answer that failed",
            not ok_bad,
            "a regression that passes its own bug guards nothing",
        )
        check(f"{reg.id} says why it caught it", bool(reasons))

        good = (
            "The refund cannot go back to the original payment method because "
            "the token was dropped during migration. It must be issued as "
            "account credit instead [HC-4003-structured-006]."
        )
        ok_good, why_not = reg.judge(good)
        check(
            f"{reg.id} allows a correct answer",
            ok_good,
            f"false alarm: {why_not}",
        )



# ---------------------------------------------------------------------------
# Week 12: the capstone. One entry point, a guide a stranger can follow, a
# demo that shows a real failure, and numbers that can be defended.
# ---------------------------------------------------------------------------
def test_w12_single_entry_point() -> None:
    """One door, and every command behind it really exists."""
    import app

    # Read the real parser rather than a copied list, so this cannot drift.
    help_text = app.build_parser().format_help()

    for command in ("doctor", "index", "ask", "demo", "eval", "logs", "report"):
        check(f"app.py offers '{command}'", command in help_text)

    check(
        "app.py --help names the first command to run",
        "doctor" in help_text and "start here" in help_text.lower(),
        "a stranger reading --help must be told where to begin",
    )

    # Every subcommand must resolve to something callable. A subparser whose
    # handler was renamed would otherwise only fail in front of an audience.
    for name in ("cmd_doctor", "cmd_index", "cmd_ask", "cmd_logs", "cmd_eval", "cmd_report"):
        check(f"{name} exists and is callable", callable(getattr(app, name, None)))

    import demo

    check("demo.run is callable", callable(getattr(demo, "run", None)))


def test_w12_entry_point_does_not_reimplement() -> None:
    """app.py is a door, not a second implementation.

    The risk of adding an entry point in the last week is that it quietly
    becomes a fork: a second retrieval path, a second prompt, a second way to
    score. Then the write-ups describe one app and the demo shows another.
    """
    from pathlib import Path

    source = Path("app.py").read_text(encoding="utf-8")

    for banned, why in (
        ("SYSTEM_PROMPT_V", "app.py must not hold its own prompt"),
        ("ChatOpenAI", "app.py must not build its own model client"),
        ("def search_by_mode", "app.py must not hold its own retrieval"),
    ):
        check(f"app.py does not redefine: {banned}", banned not in source, why)

    check(
        "app.py answers by calling the real agent loop",
        "from agent.loop import run" in source,
        "the demo must run the same code the evals scored",
    )


def test_w12_doctor_catches_a_broken_machine() -> None:
    """A doctor that always says 'ok' is worse than no doctor."""
    from pathlib import Path

    source = Path("app.py").read_text(encoding="utf-8")

    check(
        "doctor reports a non-zero exit when something is wrong",
        "return 1" in source and "problems.append" in source,
        "a stranger needs a failure they can see",
    )
    check(
        "every doctor failure carries the command that fixes it",
        source.count("fix=") >= 5,
        "naming the problem without the fix leaves them stuck",
    )


def test_w12_unchecked_marks_separates_policy_from_anecdote() -> None:
    """The seam found on a real run: two kinds of source, one kind of bracket.

    A live ticket produced an answer ending `[SUP-2041][SUP-2114]`. Those are
    real past tickets from the ticket-history server, not inventions. But the
    citation check only matches the HC-xxxx-strategy-nnn shape, so it saw
    nothing at all, and the output printed "sources: HC-4002-structured-004" as
    though the whole answer were help-centre policy.
    """
    from app import unchecked_marks

    mixed = (
        "Re-map the tax code [HC-4002-structured-004]. In past cases this "
        "failed again [SUP-2041][SUP-2114]."
    )
    marks = unchecked_marks(mixed)
    check("a past-ticket mark is reported", marks == ["SUP-2041", "SUP-2114"], str(marks))

    clean = "Issue it as account credit [HC-4003-structured-006]."
    check("a help-centre citation is not reported", unchecked_marks(clean) == [])

    check("plain text reports nothing", unchecked_marks("No brackets here.") == [])
    check("an empty answer reports nothing", unchecked_marks("") == [])

    repeated = "[SUP-2041] and again [SUP-2041]"
    check("a repeated mark is listed once", unchecked_marks(repeated) == ["SUP-2041"])


def test_w12_demo_is_free_and_shows_a_failure() -> None:
    """The demo must run with no network, and must show something going wrong."""
    from pathlib import Path

    source = Path("demo.py").read_text(encoding="utf-8")

    check(
        "the demo has four parts",
        all(f"part{n}_" in source for n in (1, 2, 3, 4)),
    )
    check(
        "part 1 replays from the log unless --live is passed",
        "if live:" in source and "store.read_all()" in source,
        "a demo that needs the network can fail for the wrong reason",
    )

    # Part 2 must run the real detector against the real failing answer, not
    # print a story about it.
    from evals.w11_regressions import REFUND_TO_CARD as R01
    from obs import plant

    ok_bad, reasons = R01.judge(R01.failing_answer)
    check("the demo's failure is still caught by the detector", not ok_bad, str(reasons))

    caught, why = plant.contradicts_its_citation(
        {"answer": R01.failing_answer, "citations": [plant.CITED_CHUNK]}
    )
    check("the demo's proof step still fires", caught, why or "silent")

    check(
        "the demo names what the numbers are NOT",
        "WHAT THESE NUMBERS ARE NOT" in source,
        "a number with no caveat cannot be defended",
    )


def test_w12_weak_spots_are_written_down() -> None:
    """Known weak spots, each with a reason and a fix."""
    from pathlib import Path

    path = Path("KNOWN_WEAK_SPOTS.md")
    check("KNOWN_WEAK_SPOTS.md exists", path.exists())
    if not path.exists():
        return

    text = path.read_text(encoding="utf-8")
    entries = text.count("\n### ")
    whys = text.count("**Why it matters:**")
    fixes = text.count("**Fix:**")

    check("at least six weak spots are named", entries >= 6, f"{entries}")
    check("every weak spot says why it matters", whys == entries, f"{whys} of {entries}")
    check("every weak spot says what the fix is", fixes == entries, f"{fixes} of {entries}")

    # The honest ones are the specific ones. A page of "could be improved" is
    # not a weak-spots page.
    for required in ("60", "kappa", "pattern", "parallel"):
        check(f"the weak spots are specific: mentions {required!r}", required in text)


def test_w12_readme_gets_a_stranger_running() -> None:
    """The fresh-eyes test, as far as a test can carry it."""
    from pathlib import Path

    readme = Path("README.md").read_text(encoding="utf-8")

    for step, why in (
        ("pip install -r requirements.txt", "they need the packages"),
        (".env", "they need to know a key is required"),
        ("python app.py doctor", "they need a way to check before they run"),
        ("python app.py index", "an empty index is the first thing that breaks"),
        ("python app.py ask", "they need to see it answer something"),
        ("python app.py demo", "they need a run that costs nothing"),
    ):
        check(f"README gives the step: {step}", step in readme, why)

    check(
        "README says which commands cost money",
        "Costs calls?" in readme or "costs calls" in readme.lower(),
        "a stranger on a free key will otherwise burn the quota on the first try",
    )
    check(
        "README links the weak spots",
        "KNOWN_WEAK_SPOTS.md" in readme,
        "the limits must be reachable from the front page",
    )
    check(
        "README explains the output, not just the commands",
        "trace" in readme and "chunk id" in readme,
        "a command list is not a guide",
    )


def test_w12_every_claimed_number_has_a_file() -> None:
    """`app.py report` must not point at a file that is not there."""
    from pathlib import Path

    import app

    source = Path("app.py").read_text(encoding="utf-8")
    check("report lists one row per week", source.count('results/w') >= 6)

    # Pull the paths out of the report table and check each one resolves.
    import re

    paths = re.findall(r'"((?:results/|KNOWN_)[^"]+\.md)"', source)
    check("report names at least eight files", len(paths) >= 8, str(len(paths)))
    missing = [p for p in paths if not Path(p).exists()]
    check("every file the report names exists", not missing, str(missing))

    check("report is callable", callable(getattr(app, "cmd_report", None)))

# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Acceptance tests.")
    parser.add_argument(
        "--with-generation",
        action="store_true",
        help="Also test citations and refusals. Needs an API key, 6 LLM calls.",
    )
    args = parser.parse_args()
    term.init()

    print(term.grey("Loading the embedding model...\n"))

    groups = [
        ("corpus", test_corpus),
        ("index", test_index),
        ("chunk metadata", test_metadata),
        ("structure-aware guarantee", test_structure_guarantee),
        ("citation resolution", test_resolvable_citations),
        ("hit-in-top-5", test_hit_rate),
        ("product_area filter", test_metadata_filter),
        ("w4 question set", test_w4_question_set),
        ("w4 keyword arm", test_keyword_arm),
        ("w4 one change only", test_one_change_only),
        ("w4 hit-rate@3 before/after", test_hybrid_improves_hit_rate),
        ("w5 traffic pool", test_w5_pool),
        ("w5 sample is not curated", test_w5_sample_is_not_curated),
        ("w5 traces are complete", test_w5_traces_are_complete),
        ("w5 notes came before the groups", test_w5_notes_came_before_the_groups),
        ("w5 taxonomy and prediction", test_w5_taxonomy_and_prediction),
        ("w7 ticket set", test_w7_tickets),
        ("w7 tools", test_w7_tools),
        ("w7 stop conditions", test_w7_stop_conditions),
        ("w7 action parser", test_w7_parser),
        ("w7 race is fair", test_w7_race_is_fair),
        ("w8 trajectory finds the gap", test_w8_trajectory_finds_the_gap),
        ("w8 quiet give-up", test_w8_quiet_give_up),
        ("w8 loop detection", test_w8_loop_detection),
        ("w8 loop guard stops a loop", test_w8_loop_guard_stops_a_loop),
        ("w8 injection scanner", test_w8_injection_scanner),
        ("w8 output validation", test_w8_output_validation),
        ("w8 least privilege", test_w8_least_privilege),
        ("w8 defence is measured", test_w8_defence_is_measured_not_assumed),
        ("w9 mcp handshake", test_w9_handshake),
        ("w9 discovery not hardcoding", test_w9_discovery_not_hardcoding),
        ("w9 bolt-on without touching the agent", test_w9_bolt_on_without_touching_the_agent),
        ("w9 recoverable errors", test_w9_recoverable_errors),
        ("w9 tool poisoning", test_w9_tool_poisoning),
        ("w9 privilege boundary moved", test_w9_privilege_boundary_moved),
        ("w9 chunk ids survive the wire", test_w9_chunk_ids_survive_the_wire),
        ("w10 race is fair", test_w10_race_is_fair),
        ("w10 meter uses provider numbers", test_w10_meter_uses_the_provider_numbers),
        ("w10 agent cards route", test_w10_agent_cards_route),
        ("w10 task lifecycle", test_w10_task_lifecycle),
        ("w10 specialists are narrow", test_w10_specialists_are_narrow),
        ("w10 verdict rule", test_w10_verdict_rule),
        ("w10 context re-send is measurable", test_w10_context_resend_is_measurable),
        ("w11 trace shape", test_w11_trace_shape),
        ("w11 meter emits spans", test_w11_meter_emits_spans),
        ("w11 log and search", test_w11_log_and_search),
        ("w11 proof step", test_w11_proof_step),
        ("w11 cache is fenced", test_w11_cache_is_fenced),
        ("w11 cost improved, risk measured", test_w11_cost_improved_and_risk_measured),
        ("w11 failure became a test", test_w11_failure_became_a_test),
        ("w12 single entry point", test_w12_single_entry_point),
        ("w12 entry point does not reimplement", test_w12_entry_point_does_not_reimplement),
        ("w12 doctor catches a broken machine", test_w12_doctor_catches_a_broken_machine),
        ("w12 policy vs anecdote at the seam", test_w12_unchecked_marks_separates_policy_from_anecdote),
        ("w12 demo is free and shows a failure", test_w12_demo_is_free_and_shows_a_failure),
        ("w12 weak spots are written down", test_w12_weak_spots_are_written_down),
        ("w12 README gets a stranger running", test_w12_readme_gets_a_stranger_running),
        ("w12 every claimed number has a file", test_w12_every_claimed_number_has_a_file),
    ]
    if args.with_generation:
        groups.append(("generation and refusal", test_generation))

    for name, fn in groups:
        print(term.bold(f"\n-- {name}"))
        try:
            fn()
        except SystemExit:
            raise
        except Exception as exc:
            check(f"{name} raised {type(exc).__name__}", False, str(exc))

    total = passed + failed
    print()
    if failed:
        print(term.paint(f"{failed} of {total} checks FAILED", "red", "bold"))
        sys.exit(1)
    print(term.paint(f"All {total} checks passed.", "green", "bold"))
    if not args.with_generation:
        print(term.grey("Generation not tested. Add --with-generation to include it."))


if __name__ == "__main__":
    main()
