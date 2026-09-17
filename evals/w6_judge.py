"""LLM-as-judge, for the two things a rule cannot decide.

WHAT THE RULES ALREADY COVER, SO THE JUDGE DOES NOT
    w6_checks.py decides, deterministically: did it answer or refuse, is there
    a resolvable citation, is any citation fabricated, does a cited chunk hold
    the required text, is the output self-contradictory. All free, all binary.

WHAT IS LEFT FOR A JUDGE
    FAITHFULNESS   Does the answer say ONLY what the cited chunks say?
        A rule can confirm the cited chunk contains the required phrase. It
        cannot see that the answer ALSO added a confident sentence the chunk
        never supported. That is the dangerous failure in a support tool: a
        correct-looking answer with one invented clause, carrying a real
        citation that appears to vouch for it.

    RELEVANCY      Does the answer address the question that was asked?
        The corpus is full of near-identical error tables. An answer about
        ERR-4044 is fluent, cited and faithful, and useless if the agent asked
        about ERR-4032. Substring rules pass it; a reader would not.

BINARY, NOT 1-10
    Both dimensions are yes/no. A 1-10 scale invites the judge to hover around
    6 and 7, and it makes agreement with a human grader almost impossible to
    measure: is a 6 against a 7 a disagreement? Binary makes the comparison in
    w6_validate_judge.py exact, which is the whole point of validating it.

THE JUDGE IS NOT TRUSTED UNTIL IT IS VALIDATED
    Nothing here should be quoted as a number until w6_validate_judge.py shows
    the judge agreeing with hand grading. That script is the gate.

EVERY JUDGEMENT IS CACHED
    Keyed by the exact inputs plus the prompt version and judge model. Re-runs
    cost nothing, and changing the prompt invalidates the cache on purpose.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from config import get_settings

# Bump when the prompt below changes. Old judgements then stop being reused,
# because they were produced by a different judge.
JUDGE_PROMPT_VERSION = "v1"

JUDGE_SYSTEM = """You grade a support assistant's answer against the source text it cited.

You will be given a QUESTION, the ANSWER, and the exact SOURCE CHUNKS the answer
cited. Judge only what is in front of you. You have no outside knowledge of the
product, and you must not use any.

Score two things, each strictly yes or no.

FAITHFUL
  yes  Every factual claim in the answer is supported by the SOURCE CHUNKS.
  no   The answer states at least one fact the chunks do not support, or
       contradicts them, or adds a specific detail (a number, a name, a step)
       that is not there.
  Paraphrasing is fine. Adding is not.

RELEVANT
  yes  The answer addresses the question that was actually asked.
  no   The answer is about a neighbouring topic. A different error code, a
       different plan, a different article. Fluent and well-sourced still
       counts as no if it answers a question nobody asked.

Reply with JSON and nothing else:

{"faithful": true, "faithful_reason": "<one short line>",
 "relevant": true, "relevant_reason": "<one short line>"}

A reason is at most 15 words. Name the specific unsupported claim when you say
no, so a human can check your verdict against the source."""

JUDGE_USER = """QUESTION:
{question}

ANSWER:
{answer}

SOURCE CHUNKS THE ANSWER CITED:
{sources}"""


@dataclass
class Judgement:
    """One judged answer, on two binary dimensions."""

    case_id: str
    faithful: bool | None = None
    relevant: bool | None = None
    faithful_reason: str = ""
    relevant_reason: str = ""
    error: str | None = None
    cached: bool = False
    raw: str = ""

    @property
    def usable(self) -> bool:
        return self.error is None and self.faithful is not None

    @property
    def passed(self) -> bool:
        return bool(self.faithful and self.relevant)

    def as_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "faithful": self.faithful,
            "relevant": self.relevant,
            "faithful_reason": self.faithful_reason,
            "relevant_reason": self.relevant_reason,
            "error": self.error,
        }


def _fingerprint(question: str, answer_text: str, sources: str, model: str) -> str:
    """Cache key. Any change to the inputs or the judge invalidates it."""
    blob = "␟".join([JUDGE_PROMPT_VERSION, model, question, answer_text, sources])
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:24]


def cited_sources(answer) -> str:
    """The exact text of every chunk the answer cited, labelled by chunk_id.

    Only cited chunks are shown, not everything retrieved. The judge's job is
    "is this answer supported by what it claims to be supported by", and
    handing it the whole context would let an unsupported claim pass because
    some other chunk happened to mention it.
    """
    blocks = []
    for cite in answer.citations:
        if cite.resolves and cite.text:
            blocks.append(f"[{cite.chunk_id}]\n{cite.text.strip()}")
    return "\n\n---\n\n".join(blocks) if blocks else "NO RESOLVABLE SOURCES WERE CITED."


class JudgeCache:
    """Judgements on disk, so a rerun never pays twice for the same verdict."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.data: dict[str, dict] = {}
        if path.exists():
            try:
                self.data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                self.data = {}

    def get(self, key: str) -> dict | None:
        return self.data.get(key)

    def put(self, key: str, value: dict) -> None:
        self.data[key] = value
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(self.data, indent=2, ensure_ascii=False), encoding="utf-8"
        )


def _parse(text: str) -> dict:
    """Pull the JSON verdict out of the reply, tolerating fences and chatter."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"no JSON object in judge reply: {text[:120]!r}")
    return json.loads(match.group(0))


def judge_answer(case: dict, answer, cache: JudgeCache | None = None) -> Judgement:
    """Judge one answer on faithfulness and relevancy.

    A refusal is never judged. There is no answer to be faithful about, and the
    rules already decide whether a refusal was correct.
    """
    settings = get_settings()
    result = Judgement(case_id=case["id"])

    if answer.refused:
        result.error = "skipped: refusal, nothing to judge"
        return result

    sources = cited_sources(answer)
    key = _fingerprint(case["question"], answer.answer, sources, settings.openrouter_model)

    if cache is not None:
        hit = cache.get(key)
        if hit is not None:
            return Judgement(
                case_id=case["id"],
                faithful=hit.get("faithful"),
                relevant=hit.get("relevant"),
                faithful_reason=hit.get("faithful_reason", ""),
                relevant_reason=hit.get("relevant_reason", ""),
                error=hit.get("error"),
                cached=True,
            )

    from rag.answerer import _llm

    try:
        reply = _llm(max_tokens=200).invoke(
            [
                ("system", JUDGE_SYSTEM),
                (
                    "human",
                    JUDGE_USER.format(
                        question=case["question"],
                        answer=answer.answer,
                        sources=sources,
                    ),
                ),
            ]
        )
        raw = (reply.content or "").strip()
        parsed = _parse(raw)
        result.raw = raw
        result.faithful = bool(parsed["faithful"])
        result.relevant = bool(parsed["relevant"])
        result.faithful_reason = str(parsed.get("faithful_reason", ""))[:160]
        result.relevant_reason = str(parsed.get("relevant_reason", ""))[:160]
    except Exception as exc:
        result.error = f"{type(exc).__name__}: {exc}"[:200]
        return result

    if cache is not None:
        cache.put(key, result.as_dict())
    return result


def summarise(judgements: list[Judgement]) -> dict:
    """Roll judgements up, counting unusable ones separately from failures."""
    usable = [j for j in judgements if j.usable]
    skipped = [j for j in judgements if not j.usable]
    n = len(usable)
    return {
        "judged": n,
        "not_judged": len(skipped),
        "faithful": sum(1 for j in usable if j.faithful),
        "relevant": sum(1 for j in usable if j.relevant),
        "both": sum(1 for j in usable if j.passed),
        "faithful_rate": round(sum(1 for j in usable if j.faithful) / n, 4) if n else 0.0,
        "relevant_rate": round(sum(1 for j in usable if j.relevant) / n, 4) if n else 0.0,
        "unfaithful_ids": sorted(j.case_id for j in usable if j.faithful is False),
        "irrelevant_ids": sorted(j.case_id for j in usable if j.relevant is False),
    }
