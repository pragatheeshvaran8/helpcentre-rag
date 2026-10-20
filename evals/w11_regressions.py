"""The failure-to-test loop: a bug found in the logs becomes a permanent check.

THE LOOP
    1. A customer complains, vaguely.
    2. The support drill finds the trace.
    3. The trace becomes a case in this file, with the answer the corpus
       actually supports written down beside it.
    4. The case runs with every other check, forever.

    Step 4 is the one that matters. A bug that is fixed but not pinned comes
    back the next time the prompt moves, and nobody notices until another
    customer complains.

WHY THE CASE RECORDS THE TRACE IT CAME FROM
    `found_in_trace` is the id the drill produced. Six months from now, when
    somebody asks why this odd-looking case exists, the log answers them. A
    regression case with no provenance gets deleted by the next person who
    tidies up.

TWO LAYERS, BECAUSE ONE OF THEM IS FREE
    DETECTOR   given this exact answer, does the check catch it? Deterministic,
               needs no model, runs on every commit. This is what actually
               guards: it fires the moment a bad answer of this shape appears,
               whether in a test or in the log.
    LIVE       ask the app the question again and score the reply. Costs a
               call, and is the honest end-to-end proof.

    The detector is the guard. The live case is the evidence.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Regression:
    """One failure, pinned so it cannot quietly return."""

    id: str
    question: str
    found_in_trace: str
    what_went_wrong: str
    # The substrings the corpus actually supports. A correct answer contains
    # them; the failing answer did not.
    must_contain: list[str]
    must_not_contain: list[str] = field(default_factory=list)
    article_id: str = ""
    # The exact answer that failed, kept so the detector can be tested against
    # a real example rather than one invented later.
    failing_answer: str = ""

    def judge(self, answer: str) -> tuple[bool, list[str]]:
        """Does this answer avoid the failure? Returns (ok, reasons it is not)."""
        flat = " ".join((answer or "").lower().split())
        reasons = []
        for needle in self.must_contain:
            if needle.lower() not in flat:
                reasons.append(f"missing: {needle!r}")
        for needle in self.must_not_contain:
            if needle.lower() in flat:
                reasons.append(f"must not say: {needle!r}")
        return (not reasons), reasons

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "question": self.question,
            "found_in_trace": self.found_in_trace,
            "what_went_wrong": self.what_went_wrong,
            "must_contain": self.must_contain,
            "must_not_contain": self.must_not_contain,
            "article_id": self.article_id,
        }


# ---------------------------------------------------------------------------
# R01 came out of the Week 11 support drill. The complaint named no trace id.
# The drill found it by date plus four words, in under three milliseconds, and
# the proof was that the answer contradicted the very chunk it cited.
REFUND_TO_CARD = Regression(
    id="R01",
    question=(
        "Customer is owed money back but their card token was dropped during "
        "the migration. Does the refund go back to the original card?"
    ),
    found_in_trace="(set by the drill)",
    what_went_wrong=(
        "The answer said the refund would go back to the customer's original "
        "card, and cited HC-4003-structured-006 while doing so. That chunk "
        "says the opposite: when the token was dropped during migration the "
        "refund cannot go back to the card and must be account credit. Every "
        "deterministic check passed it, because the citation was real. Only "
        "its agreement with the source was wrong."
    ),
    article_id="HC-4003",
    must_contain=["account credit"],
    must_not_contain=[
        "back to the original card",
        "back on the original card",
        "returned to the customer's original card",
    ],
    failing_answer=(
        "Yes. Refunds are issued back to the original payment method, so this "
        "one will be returned to the customer's original card automatically "
        "once the credit is approved [HC-4003-structured-006]. No further "
        "action is needed from you [HC-4003-structured-006]."
    ),
)

REGRESSIONS = [REFUND_TO_CARD]
BY_ID = {r.id: r for r in REGRESSIONS}


def check_all(answers: dict[str, str]) -> list[dict]:
    """Score a batch of answers, one per regression id."""
    out = []
    for reg in REGRESSIONS:
        answer = answers.get(reg.id)
        if answer is None:
            out.append({"id": reg.id, "state": "not run", "ok": None, "reasons": []})
            continue
        ok, reasons = reg.judge(answer)
        out.append(
            {"id": reg.id, "state": "ran", "ok": ok, "reasons": reasons, "answer": answer}
        )
    return out
