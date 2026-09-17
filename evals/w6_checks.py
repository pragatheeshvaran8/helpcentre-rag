"""Week 6 assertion checks: everything a rule can decide, decided by a rule.

WHY RULES FIRST
    The week's brief is explicit: "Simple checks a rule can do (is a source
    present? did it refuse when it should?) - do these first, they're free."

    Free matters here beyond cost. A rule is deterministic, so the same answer
    always scores the same, and nobody has to trust a model to grade a model.
    Every check below is binary and reproducible.

WHAT IS DELIBERATELY *NOT* HERE
    Faithfulness ("does the answer only say what the cited chunk says") and
    relevancy ("does it answer the question that was asked") cannot be decided
    by substring matching. Those live in w6_judge.py, and the judge is validated
    against hand grading before its numbers are used.

THE THREE WEEK 5 FAILURE GROUPS, AS RULES
    Week 5 read 20 traces and named three problems. All three turn out to be
    rule-checkable, which is worth saying plainly: the expensive judge is not
    needed for the headline number.

    1. "Answers with nothing you can check"  -> UNCHECKED_ANSWER
       An answer with no resolvable [chunk_id] anywhere in it.

    2. "Refuses a question the corpus can answer" -> FALSE_REFUSAL
       Refused, yet the answering chunk was in the context it was shown. This
       is the group Week 5 chose to fix, and it is fully deterministic because
       the pool records which chunk answers each question.

    3. "Prints a refusal, then answers anyway" -> REFUSAL_THEN_ANSWER
       The fixed refusal string appears, and substantive content appears with
       it. The output is internally contradictory.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from evals.w5_questions import ANSWER, REFUSE
from rag.answerer import REFUSAL_TOKEN
from rag.retriever import chunk_answers_question

# ---------------------------------------------------------------------------
# Failure modes. These are the "problem types" the before/after is reported by.
# ---------------------------------------------------------------------------
UNCHECKED_ANSWER = "unchecked_answer"
FALSE_REFUSAL = "false_refusal"
REFUSAL_THEN_ANSWER = "refusal_then_answer"
FABRICATED_CITATION = "fabricated_citation"
WRONG_SOURCE = "wrong_source"
MISSED_REFUSAL = "missed_refusal"
RETRIEVAL_MISS = "retrieval_miss"

FAILURE_MODES = (
    RETRIEVAL_MISS,
    FALSE_REFUSAL,
    UNCHECKED_ANSWER,
    FABRICATED_CITATION,
    WRONG_SOURCE,
    REFUSAL_THEN_ANSWER,
    MISSED_REFUSAL,
)

# A refusal is exactly two lines: the fixed sentence, then "Missing: ...".
# Anything beyond that is the model answering after refusing.
_MAX_REFUSAL_LINES = 3


@dataclass
class CheckResult:
    """One binary assertion."""

    name: str
    passed: bool
    detail: str = ""
    # Not every check applies to every case. A refusal case has nothing to say
    # about citations. Skipped checks never count for or against a score.
    applicable: bool = True


@dataclass
class CaseScore:
    """Every assertion for one case, plus the failure modes it triggered."""

    case_id: str
    kind: str
    expected: str
    checks: list[CheckResult] = field(default_factory=list)
    failure_modes: list[str] = field(default_factory=list)

    @property
    def applicable(self) -> list[CheckResult]:
        return [c for c in self.checks if c.applicable]

    @property
    def passed(self) -> bool:
        """A case passes only when every applicable assertion passes."""
        return all(c.passed for c in self.applicable)

    @property
    def score(self) -> float:
        """Fraction of applicable assertions passed. Used for partial credit."""
        rows = self.applicable
        return sum(1 for c in rows if c.passed) / len(rows) if rows else 1.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def context_holds_answer(answer, requirements: list[dict]) -> bool:
    """Was a chunk that satisfies a requirement actually shown to the model?

    This is what separates a retrieval failure from a generation failure, and
    it is why a false refusal can be detected without asking a judge.
    """
    for req in requirements:
        for hit in answer.retrieved:
            if hit["article_id"] == req["article_id"] and chunk_answers_question(
                hit["text"], req["must_contain"]
            ):
                return True
    return False


def citation_supports(answer, requirements: list[dict]) -> bool:
    """Did the model cite a chunk that really contains the required answer?"""
    for req in requirements:
        for cite in answer.citations:
            if (
                cite.resolves
                and cite.article_id == req["article_id"]
                and cite.text
                and chunk_answers_question(cite.text, req["must_contain"])
            ):
                return True
    return False


def looks_like_refusal_then_answer(text: str) -> bool:
    """Does the output refuse and then answer anyway?"""
    if REFUSAL_TOKEN not in text.upper():
        return False
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if len(lines) > _MAX_REFUSAL_LINES:
        return True
    # A refusal has no business carrying a citation.
    from rag.answerer import CITATION_RE

    return bool(CITATION_RE.search(text))


# ---------------------------------------------------------------------------
# The check suite
# ---------------------------------------------------------------------------
def run_checks(case: dict, answer) -> CaseScore:
    """Score one answered case against every applicable rule."""
    expected = case["expected_behaviour"]
    requirements = case.get("requirements") or []
    score = CaseScore(case_id=case["id"], kind=case["kind"], expected=expected)

    def add(name: str, passed: bool, detail: str = "", applicable: bool = True) -> None:
        score.checks.append(CheckResult(name, passed, detail, applicable))

    refused = answer.refused
    retrieved_ok = context_holds_answer(answer, requirements) if requirements else False

    # --- shared: the output must never contradict itself -------------------
    contradictory = looks_like_refusal_then_answer(answer.answer)
    add(
        "not_refusal_then_answer",
        not contradictory,
        "refusal text carries an answer" if contradictory else "",
    )
    if contradictory:
        score.failure_modes.append(REFUSAL_THEN_ANSWER)

    if expected == ANSWER:
        # --- retrieval did its job, or it did not ---------------------------
        add(
            "retrieval_put_answer_in_context",
            retrieved_ok,
            "" if retrieved_ok else "no retrieved chunk satisfies the requirement",
        )
        if not retrieved_ok:
            score.failure_modes.append(RETRIEVAL_MISS)

        # --- it must answer ------------------------------------------------
        add("answered", not refused, "refused an answerable question" if refused else "")
        if refused and retrieved_ok:
            # The answer was on screen and it refused anyway. This is the group
            # Week 5 chose to fix.
            score.failure_modes.append(FALSE_REFUSAL)

        # Citation checks only mean something once an answer exists.
        answered = not refused
        resolvable = [c for c in answer.citations if c.resolves]
        add(
            "has_resolvable_citation",
            bool(resolvable),
            "" if resolvable else "no resolvable [chunk_id] in the answer",
            applicable=answered,
        )
        if answered and not resolvable:
            score.failure_modes.append(UNCHECKED_ANSWER)

        fabricated = [c.chunk_id for c in answer.citations if not c.resolves]
        add(
            "no_fabricated_citation",
            not fabricated,
            f"unresolvable: {fabricated}" if fabricated else "",
            applicable=answered and bool(answer.citations),
        )
        if answered and fabricated:
            score.failure_modes.append(FABRICATED_CITATION)

        supported = citation_supports(answer, requirements)
        add(
            "cites_a_chunk_that_holds_the_answer",
            supported,
            "" if supported else "cited chunk does not contain the required text",
            applicable=answered and bool(requirements),
        )
        if answered and requirements and not supported:
            score.failure_modes.append(WRONG_SOURCE)

    elif expected == REFUSE:
        add(
            "refused",
            refused,
            "answered a question the corpus cannot support" if not refused else "",
        )
        if not refused:
            score.failure_modes.append(MISSED_REFUSAL)
        add(
            "refusal_names_what_is_missing",
            "missing:" in answer.answer.lower(),
            "",
            applicable=refused,
        )

    return score


def aggregate(scores: list[CaseScore]) -> dict:
    """Roll case scores up into the numbers the write-up reports."""
    total = len(scores)
    by_kind: dict[str, dict] = {}
    for s in scores:
        row = by_kind.setdefault(s.kind, {"n": 0, "passed": 0})
        row["n"] += 1
        row["passed"] += int(s.passed)

    mode_counts = {m: 0 for m in FAILURE_MODES}
    for s in scores:
        for m in s.failure_modes:
            mode_counts[m] = mode_counts.get(m, 0) + 1

    return {
        "cases": total,
        "passed": sum(1 for s in scores if s.passed),
        "pass_rate": round(sum(1 for s in scores if s.passed) / total, 4) if total else 0.0,
        "mean_assertion_score": round(sum(s.score for s in scores) / total, 4) if total else 0.0,
        "by_kind": {
            k: {**v, "pass_rate": round(v["passed"] / v["n"], 4)}
            for k, v in sorted(by_kind.items())
        },
        "failure_modes": mode_counts,
        "failing_case_ids": sorted(s.case_id for s in scores if not s.passed),
    }
