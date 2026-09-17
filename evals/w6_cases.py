"""The Week 6 eval set: the Week 5 pool, plus last week's failures as regressions.

THE EVAL SET IS THE WEEK 5 POOL
    60 questions, 9 traffic kinds, every one with a known-correct article and
    the literal text that must appear. Reusing it is deliberate. A fresh set
    would make the Week 5 numbers incomparable, and the pool already has the
    property that matters: every case can be scored without a human reading it.

REGRESSIONS: LAST WEEK'S REAL FAILURES, PINNED
    The mentor checklist asks "are last week's real failures included as tests?"
    Week 5 read 20 traces and 6 came out wrong. Those 6 are listed below by the
    pool question they came from, together with the specific failure mode that
    must never come back.

    A regression is not just "this case should pass". It is "this case must not
    fail in THIS way again". Pinning the mode is what makes the test meaningful:
    if T10 starts failing for a brand new reason, that is a different bug and
    the report should say so rather than quietly reusing the old label.
"""
from __future__ import annotations

from evals.w5_questions import POOL_BY_ID, W5_POOL
from evals.w6_checks import (
    FALSE_REFUSAL,
    REFUSAL_THEN_ANSWER,
    UNCHECKED_ANSWER,
)

# trace_id, pool question id, the mode that must not recur, what was seen.
_REGRESSIONS: list[tuple[str, str, str, str]] = [
    ("T02", "P17", REFUSAL_THEN_ANSWER,
     "Printed the fixed refusal and then answered anyway, in the same output."),
    ("T04", "P23", UNCHECKED_ANSWER,
     "Correct answer lifted from the top chunk, with no [chunk_id] anywhere."),
    ("T09", "P42", UNCHECKED_ANSWER,
     "Named its source in words, 'the migration status codes table', which "
     "cannot be resolved."),
    ("T10", "P34", FALSE_REFUSAL,
     "Asked to be walked through a procedure. The corpus has a one-line fix, "
     "and the answering chunk was in context. Refused anyway."),
    ("T11", "P02", FALSE_REFUSAL,
     "The answering chunk sat at rank 2 behind a look-alike code. Refused."),
    ("T19", "P31", FALSE_REFUSAL,
     "Asked 'can I'. The corpus states what the agent should do instead. "
     "Refused rather than answering the substance."),
]

REGRESSIONS: list[dict] = [
    {
        "trace_id": trace_id,
        "question_id": question_id,
        "banned_mode": mode,
        "seen_in_week_5": seen,
    }
    for trace_id, question_id, mode, seen in _REGRESSIONS
]

REGRESSION_BY_QUESTION: dict[str, dict] = {r["question_id"]: r for r in REGRESSIONS}


def eval_set() -> list[dict]:
    """Every case to score, annotated with its regression status."""
    cases: list[dict] = []
    for question in W5_POOL:
        reg = REGRESSION_BY_QUESTION.get(question["id"])
        cases.append(
            {
                **question,
                "is_regression": reg is not None,
                "regression_trace": reg["trace_id"] if reg else None,
                "banned_mode": reg["banned_mode"] if reg else None,
                "seen_in_week_5": reg["seen_in_week_5"] if reg else None,
            }
        )
    return cases


def regression_verdict(case: dict, failure_modes: list[str]) -> str | None:
    """Did a pinned regression come back, or break in a new way?

    Returns None for a non-regression case. Otherwise one of:
        "held"       the old failure did not recur and the case passes
        "recurred"   the exact Week 5 failure mode is back
        "new_break"  the case fails, but for a different reason
    """
    if not case.get("is_regression"):
        return None
    if case["banned_mode"] in failure_modes:
        return "recurred"
    return "new_break" if failure_modes else "held"


def _self_check() -> None:
    """Every regression must point at a real pool question."""
    missing = [r["question_id"] for r in REGRESSIONS if r["question_id"] not in POOL_BY_ID]
    assert not missing, f"regressions reference unknown pool ids: {missing}"
    ids = [r["question_id"] for r in REGRESSIONS]
    assert len(set(ids)) == len(ids), "duplicate regression question id"
    assert len(eval_set()) == len(W5_POOL)


_self_check()
