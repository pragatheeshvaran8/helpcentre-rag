"""Scoring one race: speed, cost, reliability, and how much of a ticket got answered.

THE THREE HEADLINE NUMBERS THE WEEK ASKS FOR
    SPEED        Wall-clock seconds per ticket. Reported as a median, because
                 one provider stall would move a mean and tell you nothing
                 about the usual case.
    COST         LLM calls. Not tokens: a call is the unit that is billed, rate
                 limited, and that you can count by hand from the step log.
    RELIABILITY  Two things, kept separate. Did it pass the Week 6 assertion
                 checks, and did it actually finish rather than run out of
                 budget.

THE FOURTH NUMBER, WHICH MATTERS MORE THAN ANY OF THEM
    PART COVERAGE. A ticket that asks two things is not half right when one is
    answered, it is wrong, and every ordinary pass/fail metric hides that.

    The Week 6 checks were built for one-question cases, so
    `context_holds_answer` returns True as soon as ANY requirement is met. On a
    three-part ticket that is far too generous. So coverage is computed here,
    per requirement, and it is the number the recommendation rests on.

WHY SCORING IS IN ITS OWN FILE
    run_race.py runs things and costs money. This file only reads records. It
    can be re-run over a cache for free, which is what makes it safe to change
    a metric after the expensive part is already done.
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field

from evals.w6_checks import run_checks
from evals.w7_tickets import MULTI, REFUSE, SHAPES, SINGLE
from rag.retriever import chunk_answers_question

AGENT = "agent"
WORKFLOW = "workflow"
RUNNERS = (AGENT, WORKFLOW)


@dataclass
class Coverage:
    """How many of a ticket's separate parts were actually dealt with."""

    retrieved: int = 0
    cited: int = 0
    total: int = 0

    @property
    def fully_retrieved(self) -> bool:
        return self.total > 0 and self.retrieved == self.total

    @property
    def fully_cited(self) -> bool:
        return self.total > 0 and self.cited == self.total

    def as_dict(self) -> dict:
        return {
            "retrieved": self.retrieved,
            "cited": self.cited,
            "total": self.total,
            "fully_retrieved": self.fully_retrieved,
            "fully_cited": self.fully_cited,
        }


def part_coverage(result, ticket: dict) -> Coverage:
    """Per requirement: was it put on screen, and was it actually cited?

    RETRIEVED means some chunk the runner saw satisfies that requirement. For
    the agent that is the union of everything every tool returned. For the
    fixed workflow it is the single top-k. That difference is exactly what the
    race is about, so it is deliberately not normalised away.

    CITED is stricter, and it is the one that matters to a support agent
    reading the reply: the answer named a chunk that really holds that part.
    """
    requirements = ticket.get("requirements") or []
    cover = Coverage(total=len(requirements))

    for req in requirements:
        if any(
            hit.get("article_id") == req["article_id"]
            and chunk_answers_question(hit.get("text", ""), req["must_contain"])
            for hit in result.retrieved
        ):
            cover.retrieved += 1

        if any(
            getattr(cite, "resolves", False)
            and getattr(cite, "article_id", None) == req["article_id"]
            and getattr(cite, "text", None)
            and chunk_answers_question(cite.text, req["must_contain"])
            for cite in result.citations
        ):
            cover.cited += 1

    return cover


@dataclass
class TicketScore:
    """One ticket, one runner, fully scored."""

    ticket_id: str
    shape: str
    runner: str
    passed: bool
    failure_modes: list[str]
    coverage: Coverage
    seconds: float
    llm_calls: int
    steps: int
    stop_reason: str
    refused: bool
    completed: bool
    error: str | None = None

    def as_dict(self) -> dict:
        return {
            "ticket_id": self.ticket_id,
            "shape": self.shape,
            "runner": self.runner,
            "passed": self.passed,
            "failure_modes": self.failure_modes,
            "coverage": self.coverage.as_dict(),
            "seconds": self.seconds,
            "llm_calls": self.llm_calls,
            "steps": self.steps,
            "stop_reason": self.stop_reason,
            "refused": self.refused,
            "completed": self.completed,
            "error": self.error,
        }


def score(ticket: dict, result) -> TicketScore:
    """Apply the Week 6 checks, then add the Week 7 coverage on top."""
    checks = run_checks(ticket, result)
    return TicketScore(
        ticket_id=ticket["id"],
        shape=ticket["shape"],
        runner=result.runner,
        passed=checks.passed,
        failure_modes=list(checks.failure_modes),
        coverage=part_coverage(result, ticket),
        seconds=result.elapsed_s,
        llm_calls=result.llm_calls,
        steps=len(result.steps),
        stop_reason=result.stop_reason,
        refused=result.refused,
        completed=result.completed,
        error=result.error,
    )


# ---------------------------------------------------------------------------
# Rolling up
# ---------------------------------------------------------------------------
def summarise(scores: list[TicketScore]) -> dict:
    """One runner's numbers. Medians for time, totals for cost."""
    if not scores:
        return {"n": 0}

    times = [s.seconds for s in scores]
    multi = [s for s in scores if s.shape == MULTI]

    def cover_rate(rows: list[TicketScore], attr: str) -> float:
        got = sum(getattr(r.coverage, attr) for r in rows)
        total = sum(r.coverage.total for r in rows)
        return round(got / total, 4) if total else 0.0

    return {
        "n": len(scores),
        "passed": sum(1 for s in scores if s.passed),
        "pass_rate": round(sum(1 for s in scores if s.passed) / len(scores), 4),
        # Speed
        "median_seconds": round(statistics.median(times), 2),
        "total_seconds": round(sum(times), 2),
        "slowest_seconds": round(max(times), 2),
        # Cost
        "llm_calls": sum(s.llm_calls for s in scores),
        "calls_per_ticket": round(sum(s.llm_calls for s in scores) / len(scores), 2),
        "steps": sum(s.steps for s in scores),
        # Reliability
        "completed": sum(1 for s in scores if s.completed),
        "stop_reasons": _tally(s.stop_reason for s in scores),
        "failure_modes": _tally(m for s in scores for m in s.failure_modes),
        "errors": sum(1 for s in scores if s.error),
        # Coverage, overall and on the shape that needs several steps
        "parts_retrieved_rate": cover_rate(scores, "retrieved"),
        "parts_cited_rate": cover_rate(scores, "cited"),
        "multi_parts_cited_rate": cover_rate(multi, "cited"),
        "multi_fully_cited": sum(1 for s in multi if s.coverage.fully_cited),
        "multi_n": len(multi),
        "by_shape": {
            shape: _shape_row([s for s in scores if s.shape == shape]) for shape in SHAPES
        },
    }


def _shape_row(rows: list[TicketScore]) -> dict:
    if not rows:
        return {"n": 0, "passed": 0, "median_seconds": 0.0, "llm_calls": 0}
    return {
        "n": len(rows),
        "passed": sum(1 for r in rows if r.passed),
        "median_seconds": round(statistics.median([r.seconds for r in rows]), 2),
        "llm_calls": sum(r.llm_calls for r in rows),
        "fully_cited": sum(1 for r in rows if r.coverage.fully_cited),
    }


def _tally(items) -> dict:
    out: dict[str, int] = {}
    for item in items:
        out[item] = out.get(item, 0) + 1
    return dict(sorted(out.items(), key=lambda kv: (-kv[1], kv[0])))


# ---------------------------------------------------------------------------
# The recommendation
# ---------------------------------------------------------------------------
@dataclass
class Verdict:
    """Which one to ship, and the reason, derived rather than asserted.

    The rule is written down before the numbers are in, and it is applied
    mechanically. A recommendation chosen after seeing the result is not a
    recommendation, it is a preference with a table attached.
    """

    ship: str
    reason: str
    per_shape: dict = field(default_factory=dict)


def recommend(agent: dict, workflow: dict) -> Verdict:
    """Pick a runner by the rule below, not by taste.

    The rule, in order:

    1. If one runner covers materially more of the multi-part tickets, it wins
       those tickets. Answering half a ticket is the failure this week is about,
       and no amount of speed compensates for it.
    2. On single-part tickets, cost breaks the tie, because both should be
       reaching the same answer and the only difference is what it took.
    3. Overall, prefer the cheaper one unless the multi-part gap is real.

    "Materially" is one whole ticket. A gap of zero fully-answered tickets is
    noise on a set this size, and saying so is more useful than a decimal.
    """
    per_shape = {}
    a_multi = agent.get("multi_fully_cited", 0)
    w_multi = workflow.get("multi_fully_cited", 0)
    multi_n = agent.get("multi_n", 0)

    per_shape[MULTI] = (
        AGENT if a_multi > w_multi else WORKFLOW if w_multi > a_multi else "tie"
    )

    a_single = agent["by_shape"].get(SINGLE, {})
    w_single = workflow["by_shape"].get(SINGLE, {})
    if a_single.get("passed", 0) != w_single.get("passed", 0):
        per_shape[SINGLE] = (
            AGENT if a_single["passed"] > w_single["passed"] else WORKFLOW
        )
    else:
        per_shape[SINGLE] = (
            WORKFLOW if w_single.get("llm_calls", 0) <= a_single.get("llm_calls", 0) else AGENT
        )

    a_ref = agent["by_shape"].get(REFUSE, {})
    w_ref = workflow["by_shape"].get(REFUSE, {})
    per_shape[REFUSE] = (
        AGENT
        if a_ref.get("passed", 0) > w_ref.get("passed", 0)
        else WORKFLOW
        if w_ref.get("passed", 0) > a_ref.get("passed", 0)
        else "tie"
    )

    gap = a_multi - w_multi
    if gap >= 1:
        ship = AGENT
        reason = (
            f"The agent fully answers {a_multi} of {multi_n} multi-part tickets against "
            f"{w_multi} for the fixed workflow. It costs "
            f"{agent['calls_per_ticket']} calls a ticket against "
            f"{workflow['calls_per_ticket']}, and is "
            f"{_ratio(agent['median_seconds'], workflow['median_seconds'])} slower. "
            "Half an answer on a support ticket is a failure, so the coverage gap "
            "is worth the cost."
        )
    elif gap <= -1:
        ship = WORKFLOW
        reason = (
            f"The fixed workflow fully answers {w_multi} of {multi_n} multi-part tickets "
            f"against {a_multi} for the agent, and does it for "
            f"{workflow['calls_per_ticket']} calls a ticket against "
            f"{agent['calls_per_ticket']}. The loop is losing on the shape it was "
            "supposed to win."
        )
    else:
        ship = WORKFLOW
        reason = (
            f"Both fully answer {a_multi} of {multi_n} multi-part tickets, so the loop "
            "buys no coverage. It costs "
            f"{agent['calls_per_ticket']} calls a ticket against "
            f"{workflow['calls_per_ticket']}, runs "
            f"{_ratio(agent['median_seconds'], workflow['median_seconds'])} slower, and can "
            "overrun its budget, which a fixed sequence cannot. Ship the simple one."
        )
    return Verdict(ship=ship, reason=reason, per_shape=per_shape)


def _ratio(a: float, b: float) -> str:
    if not b:
        return "immeasurably"
    return f"{a / b:.1f}x"
