"""The fixed workflow. The thing the agent has to beat.

WHAT IT IS
    Retrieve once on the whole ticket, answer once, stop. Two steps, always the
    same two, in the same order. Exactly the app Weeks 3 to 6 built and tuned,
    wrapped so the race can run it and score it beside the agent.

WHY THIS IS THE RIGHT BASELINE AND NOT A STRAW MAN
    It would be easy to make the agent look good by racing it against something
    deliberately weak. This is the opposite: it is six weeks of work. Hybrid
    retrieval from Week 4, the structure-aware chunker from Week 3, and the
    prompt that Week 6 measured from 46.5% to 79.1%. If the agent cannot beat
    this, that is the finding, and it is the finding the week is asking for.

WHAT IT CANNOT DO, BY CONSTRUCTION
    One retrieval, on the ticket's full text. When a ticket asks two unrelated
    things, both go into one query, and top-k has to cover both topics at once.
    There is no second look. That is the weakness the agent is supposed to
    exploit, and whether it actually does is a measurement, not an assumption.

WHY IT IS NOT JUST `answer_question`
    It is. The only thing this file adds is the timing, the call count and the
    same result shape the agent returns, so the two can be put in one table.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

from agent.budget import FINISHED
from agent.memory import Step
from config import STRATEGY_STRUCTURED
from evals.w5_questions import W5_K


@dataclass
class WorkflowRun:
    """Same shape as AgentRun, so one scorer reads both."""

    question: str
    answer: str = ""
    refused: bool = False
    retrieved: list[dict] = field(default_factory=list)
    citations: list = field(default_factory=list)
    gate_fired: bool = False
    budget_degraded: bool = False

    runner: str = "workflow"
    steps: list[Step] = field(default_factory=list)
    stop_reason: str = FINISHED
    llm_calls: int = 0
    elapsed_s: float = 0.0
    error: str | None = None

    @property
    def completed(self) -> bool:
        return self.stop_reason == FINISHED


def run(ticket: str, *, verbose: bool = False) -> WorkflowRun:
    """Retrieve once, answer once. No decisions, no loop, no budget needed.

    There is no budget argument on purpose. A fixed sequence cannot overrun,
    which is one of the things the race is measuring. Adding a limit it can
    never hit would only make the two look more alike than they are.
    """
    from rag.answerer import answer_question

    started = time.monotonic()
    result = WorkflowRun(question=ticket)

    try:
        answer = answer_question(ticket, STRATEGY_STRUCTURED, k=W5_K, use_gate=True)
    except Exception as exc:
        result.stop_reason = "error"
        result.error = f"{type(exc).__name__}: {exc}"[:300]
        result.elapsed_s = round(time.monotonic() - started, 2)
        return result

    result.answer = answer.answer
    result.refused = answer.refused
    result.retrieved = answer.retrieved
    result.citations = answer.citations
    result.gate_fired = answer.gate_fired
    result.budget_degraded = answer.budget_degraded
    # The gate refuses without calling the model at all, which is the whole
    # point of having it, so the cost of a gated refusal really is zero.
    result.llm_calls = 0 if answer.gate_fired else 1
    result.elapsed_s = round(time.monotonic() - started, 2)

    result.steps = [
        Step(
            n=1,
            thought="fixed: retrieve on the whole ticket",
            tool="search_help_centre",
            args={"query": ticket},
            observation=f"{len(answer.retrieved)} chunk(s) retrieved",
        ),
        Step(
            n=2,
            thought="fixed: answer from what was retrieved",
            tool="finish",
            args={},
            observation=answer.answer,
        ),
    ]
    if verbose:
        print(f"  step 1: retrieve -> {len(answer.retrieved)} chunks")
        print(f"  step 2: answer ({'refused' if answer.refused else 'answered'})")
    return result
