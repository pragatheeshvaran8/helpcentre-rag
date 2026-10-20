"""The planted bad answer, for the support drill.

TRACK A: "find the refund answer nobody logged a trace id for"

WHAT IS PLANTED, AND WHY THIS SHAPE
    A customer's card token was dropped during the migration. They ask whether
    their refund goes back to the card. The help centre is explicit:

        "If the token was dropped during migration, the refund cannot be
        returned to the card and must be issued as account credit instead."
                                              -- HC-4003-structured-006

    The planted answer says the opposite: it tells the agent to refund to the
    original card. And it CITES HC-4003-structured-006 while doing so.

WHY NOT AN EASIER PLANT
    An uncited answer, or a refusal, or an obvious error would be found by a
    single filter. That would prove the filter works and nothing else.

    This one is the failure that actually reaches customers: fluent, confident,
    carrying a real citation that appears to vouch for it. Week 6 named this
    `unchecked_answer`, and it is the reason the judge exists at all. Every
    deterministic check in this project passes it, because every one of them
    asks whether the cited chunk is real rather than whether it agrees.

    So the drill cannot be won by a flag. It has to be won by searching.

HOW IT IS KEPT HONEST
    The trace carries `"planted": true` in its config. Nothing in the drill
    reads that field, and a test asserts the search never filters on it.
    Without the marker the log would contain a fabricated record with no way to
    tell it from a real one, which is a worse habit than any drill is worth.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from obs import store

# The chunk the planted answer cites, and what that chunk actually says.
CITED_CHUNK = "HC-4003-structured-006"
WHAT_THE_CORPUS_SAYS = (
    "the refund cannot be returned to the card and must be issued as account "
    "credit instead"
)

# The complaint a support lead would actually forward. Vague on purpose: no
# trace id, no date, no exact wording, and the customer's word ("refund") is
# not necessarily the word the question used.
COMPLAINT = (
    "Finance flagged something from about a week ago. Someone asked us about a "
    "refund where the card had been lost in the migration, and we apparently "
    "told them it would go back on the original card. Finance says that is "
    "wrong and it should have been account credit. No ticket number, sorry."
)

PLANTED_QUESTION = (
    "Customer is owed money back but their card token was dropped during the "
    "migration. Does the refund go back to the original card?"
)

PLANTED_ANSWER = (
    "Yes. Refunds are issued back to the original payment method, so this one "
    "will be returned to the customer's original card automatically once the "
    "credit is approved [HC-4003-structured-006]. No further action is needed "
    "from you [HC-4003-structured-006]."
)


def plant(*, days_ago: int = 7) -> dict:
    """Write the bad answer into the log. Returns the trace as written."""
    from agent.meter import USD_PER_MILLION_INPUT, USD_PER_MILLION_OUTPUT
    from obs.trace import new_trace_id

    at = (datetime.now(timezone.utc) - timedelta(days=days_ago)).replace(
        hour=14, minute=37, second=12, microsecond=0
    )

    spans = [
        {"name": "agent:step 1", "ms": 4820.0, "input_tokens": 1180, "output_tokens": 58,
         "cost": 0.0, "detail": "step 1", "ok": True, "measured": True},
        {"name": "tool:search_help_centre", "ms": 311.0, "input_tokens": 0,
         "output_tokens": 0, "cost": 0.0, "detail": "3 chunk(s)", "ok": True, "measured": True},
        {"name": "agent:step 2", "ms": 6140.0, "input_tokens": 1944, "output_tokens": 96,
         "cost": 0.0, "detail": "step 2", "ok": True, "measured": True},
    ]
    for span in spans:
        span["cost"] = round(
            span["input_tokens"] / 1_000_000 * USD_PER_MILLION_INPUT
            + span["output_tokens"] / 1_000_000 * USD_PER_MILLION_OUTPUT,
            8,
        )

    row = {
        "trace_id": new_trace_id(),
        "at": at.isoformat(),
        "question": PLANTED_QUESTION,
        "answer": PLANTED_ANSWER,
        "runner": "agent",
        "refused": False,
        "chunk_ids": [CITED_CHUNK, "HC-4003-structured-004", "HC-4002-structured-005"],
        "citations": [CITED_CHUNK],
        "cache_hit": False,
        "cache_source": "",
        "ms": round(sum(s["ms"] for s in spans), 1),
        "input_tokens": sum(s["input_tokens"] for s in spans),
        "output_tokens": sum(s["output_tokens"] for s in spans),
        "total_tokens": sum(s["input_tokens"] + s["output_tokens"] for s in spans),
        "cost": round(sum(s["cost"] for s in spans), 8),
        "llm_calls": 2,
        "spans": spans,
        "config": {
            # Marked so the log never holds an unlabelled fabrication. Nothing
            # in the drill reads this, and a test asserts that.
            "planted": True,
            "runner": "agent",
            "stop_reason": "finished",
        },
        "error": None,
    }
    store.write(row)
    return row


def contradicts_its_citation(trace: dict) -> tuple[bool, str]:
    """Does the answer say the opposite of the chunk it cites?

    This is the proof that closes the drill. A support engineer cannot hand a
    trace id to an angry customer on a hunch; they need the line from the
    article beside the line from the answer.

    Deliberately narrow. It checks this one rule rather than pretending to be a
    general faithfulness judge, because a general one is what Week 6 built and
    refused to trust.
    """
    from config import STRATEGY_STRUCTURED
    from rag.keyword import get_record

    # Whitespace is normalised on both sides. The corpus wraps its lines, so a
    # rule that reads as one sentence is two fragments to a substring match:
    # "the refund cannot be" ends a line and "returned to the card" starts the
    # next. The first version of this check silently returned False for exactly
    # that reason, and a drill whose proof step quietly fails is worse than no
    # proof step.
    def flat(text: str) -> str:
        return " ".join((text or "").lower().split())

    answer = flat(trace.get("answer"))
    for chunk_id in trace.get("citations") or []:
        record = get_record(STRATEGY_STRUCTURED, chunk_id)
        if record is None:
            continue
        body = flat(record[0])
        if WHAT_THE_CORPUS_SAYS not in body:
            continue
        says_card = any(
            phrase in answer
            for phrase in ("back to the original card", "back on the original card",
                           "returned to the customer's original card",
                           "original payment method, so this one")
        )
        mentions_credit = "account credit" in answer
        if says_card and not mentions_credit:
            return True, (
                f"{chunk_id} says: \"{WHAT_THE_CORPUS_SAYS}\". "
                "The answer says the money goes back to the original card, and "
                "never mentions account credit."
            )
    return False, ""
