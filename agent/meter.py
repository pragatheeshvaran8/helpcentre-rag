"""Token and cost accounting, so the race is settled by numbers.

WHY THIS EXISTS
    Week 7 raced the agent against a fixed workflow on calls and seconds. That
    was enough then, because both sides sent prompts of roughly the same size.

    A team of agents is different. The expensive thing about a hand-off is not
    the extra call, it is that the WHOLE context goes again: the ticket, the
    instructions, the tool catalogue, and whatever the previous specialist
    found. Counting calls hides that completely. Counting tokens is the only
    way to see it.

WHAT IS MEASURED
    input tokens    what we sent. This is where a team gets expensive.
    output tokens   what came back.
    cost            what the provider says it charged.

    All three come from the provider's own usage report, not from an estimate.
    A tokeniser on our side would be a guess about the model's tokeniser, and a
    guess is not evidence.

ABOUT COST ON THIS TIER
    The model is `:free`, so the provider reports a cost of exactly 0. That
    number is true and useless for a comparison, so `priced_cost` also exists:
    it applies a published per-million rate to the real token counts. It is
    clearly labelled as an estimate everywhere it appears, because it is
    arithmetic on a rate card rather than a bill.

WHY A SHARED METER AND NOT TWO
    Both runners record through this one object. If each side counted its own
    way, the race would measure the counters.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# A published rate, used only to turn free-tier token counts into a comparable
# money figure. Chosen as a mid-market price so neither side is flattered; the
# RATIO between the two runners is what matters, and that is rate-independent.
USD_PER_MILLION_INPUT = 0.15
USD_PER_MILLION_OUTPUT = 0.60


@dataclass
class Call:
    """One LLM call, with who made it and what it cost."""

    who: str
    purpose: str
    input_tokens: int = 0
    output_tokens: int = 0
    reported_cost: float = 0.0
    seconds: float = 0.0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def as_dict(self) -> dict:
        return {
            "who": self.who,
            "purpose": self.purpose,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "reported_cost": self.reported_cost,
            "seconds": round(self.seconds, 2),
        }


@dataclass
class Meter:
    """Every call made while answering one ticket."""

    calls: list[Call] = field(default_factory=list)

    # Week 11. When set, every recorded call also becomes a span on this trace.
    # Hung off the meter rather than added as a second hook, because the meter
    # already sees every call and two independent counters would eventually
    # disagree about the same request.
    trace: object | None = None

    def record(self, who: str, purpose: str, response, seconds: float = 0.0) -> Call:
        """Pull the provider's own usage numbers off a reply."""
        usage = getattr(response, "usage_metadata", None) or {}
        meta = (getattr(response, "response_metadata", None) or {}).get("token_usage", {})

        call = Call(
            who=who,
            purpose=purpose,
            input_tokens=int(usage.get("input_tokens") or meta.get("prompt_tokens") or 0),
            output_tokens=int(usage.get("output_tokens") or meta.get("completion_tokens") or 0),
            reported_cost=float(meta.get("cost") or 0.0),
            seconds=seconds,
        )
        self.calls.append(call)

        if self.trace is not None:
            span = self.trace.span(f"{who}:{purpose}")
            span.close(
                ms=round(seconds * 1000, 1),
                input_tokens=call.input_tokens,
                output_tokens=call.output_tokens,
                # The provider reports 0 on a free model, so the span carries
                # the priced estimate instead. Labelled as an estimate in the
                # report, never presented as a bill.
                cost=(
                    call.input_tokens / 1_000_000 * USD_PER_MILLION_INPUT
                    + call.output_tokens / 1_000_000 * USD_PER_MILLION_OUTPUT
                ),
                detail=purpose,
            )
        return call

    # -- totals -----------------------------------------------------------
    @property
    def n_calls(self) -> int:
        return len(self.calls)

    @property
    def input_tokens(self) -> int:
        return sum(c.input_tokens for c in self.calls)

    @property
    def output_tokens(self) -> int:
        return sum(c.output_tokens for c in self.calls)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def reported_cost(self) -> float:
        return sum(c.reported_cost for c in self.calls)

    @property
    def priced_cost(self) -> float:
        """An ESTIMATE. Real token counts, a published rate, not a bill."""
        return (
            self.input_tokens / 1_000_000 * USD_PER_MILLION_INPUT
            + self.output_tokens / 1_000_000 * USD_PER_MILLION_OUTPUT
        )

    def by_who(self) -> dict:
        """Tokens per participant. This is where a hand-off shows its cost."""
        out: dict[str, dict] = {}
        for call in self.calls:
            row = out.setdefault(
                call.who, {"calls": 0, "input_tokens": 0, "output_tokens": 0}
            )
            row["calls"] += 1
            row["input_tokens"] += call.input_tokens
            row["output_tokens"] += call.output_tokens
        return out

    def as_dict(self) -> dict:
        return {
            "calls": self.n_calls,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "reported_cost": round(self.reported_cost, 6),
            "priced_cost_estimate": round(self.priced_cost, 6),
            "by_who": self.by_who(),
            "per_call": [c.as_dict() for c in self.calls],
        }


def metered_invoke(llm, messages, meter: Meter | None, who: str, purpose: str):
    """Invoke, retry the transient 429s, and record what it cost.

    The retry behaviour is the Week 8 one, unchanged. A retried call is
    recorded once, when it finally succeeds, because the failed attempts
    returned no tokens and billing them to either runner would be wrong.
    """
    import time

    from rag.answerer import invoke_with_retry

    started = time.monotonic()
    response = invoke_with_retry(llm, messages)
    if meter is not None:
        meter.record(who, purpose, response, time.monotonic() - started)
    return response
