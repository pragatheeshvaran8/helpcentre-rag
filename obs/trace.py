"""What gets recorded for every request, and what makes it replayable.

THE RULE THIS FILE EXISTS FOR
    If it is not logged, it did not happen. A customer who says "it gave a
    wrong answer yesterday" is not giving you a trace id. They are giving you a
    vague sentence and a rough date, and the log is the only way back to the
    request.

WHAT A TRACE HOLDS, AND WHY EACH FIELD EARNS ITS PLACE
    trace_id      a handle. Printed in the answer so a user CAN quote it, and
                  present even when they cannot.
    at            when. The only thing a vague complaint reliably gives you.
    question      what was asked. Searchable, because a complaint paraphrases
                  the question rather than quoting it.
    answer        what was said. The thing being complained about.
    chunk_ids     what the answer was built from. Without this you cannot tell
                  a retrieval failure from a generation failure.
    citations     what it claimed as its source.
    spans         each step: name, milliseconds, tokens, cost. Not one lump,
                  because "it was slow" and "it was expensive" are usually
                  about one step, not the whole request.
    config        model, prompt fingerprint, corpus fingerprint, runner. A
                  trace you cannot reproduce is an anecdote.

WHY SPANS AND NOT ONE TOTAL
    Week 10 learned this the hard way in reverse: the squad looked cheap on
    total tokens and was twice as expensive in calls. One number hides where
    the money went. A span per step is what made "the manager spends 5,174
    input tokens and produces no answer" sayable.

REPLAY
    `replay_config` returns the settings a trace was produced under. Comparing
    it to the current config is how you find out whether a complaint is about
    behaviour that still exists. Six weeks of this project turned on exactly
    that question.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone


def new_trace_id() -> str:
    """Short, unique, and safe to read aloud down a phone line.

    Twelve hex characters, not a full UUID. A support agent has to be able to
    read it to a customer and a customer has to be able to read it back, and
    nobody does that with 36 characters.
    """
    return uuid.uuid4().hex[:12]


@dataclass
class Span:
    """One step inside a request, with what it cost."""

    name: str
    started: float = field(default_factory=time.monotonic)
    ms: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    cost: float = 0.0
    detail: str = ""
    ok: bool = True

    def close(self, **fields) -> "Span":
        self.ms = round((time.monotonic() - self.started) * 1000, 1)
        for key, value in fields.items():
            setattr(self, key, value)
        return self

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "ms": self.ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cost": round(self.cost, 8),
            "detail": self.detail[:200],
            "ok": self.ok,
        }


@dataclass
class Trace:
    """One request, start to finish, in a form you can search and replay."""

    trace_id: str = field(default_factory=new_trace_id)
    at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    question: str = ""
    answer: str = ""
    runner: str = "agent"
    refused: bool = False

    chunk_ids: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    spans: list[Span] = field(default_factory=list)
    config: dict = field(default_factory=dict)

    # Set when an answer came from cache rather than the model. Without this
    # field a cache hit looks like a free model call, and the cost saving
    # cannot be told apart from the model suddenly getting cheaper.
    cache_hit: bool = False
    cache_source: str = ""

    error: str | None = None
    _started: float = field(default_factory=time.monotonic, repr=False)

    def span(self, name: str) -> Span:
        """Open a span. Close it with .close() when the step finishes."""
        s = Span(name=name)
        self.spans.append(s)
        return s

    # -- totals, derived rather than stored, so they cannot disagree ------
    @property
    def ms(self) -> float:
        return round((time.monotonic() - self._started) * 1000, 1)

    @property
    def input_tokens(self) -> int:
        return sum(s.input_tokens for s in self.spans)

    @property
    def output_tokens(self) -> int:
        return sum(s.output_tokens for s in self.spans)

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    @property
    def cost(self) -> float:
        return sum(s.cost for s in self.spans)

    @property
    def llm_calls(self) -> int:
        """Spans that actually went to the model. A cache hit is not a call."""
        return sum(1 for s in self.spans if s.input_tokens or s.output_tokens)

    def as_dict(self) -> dict:
        return {
            "trace_id": self.trace_id,
            "at": self.at,
            "question": self.question,
            "answer": self.answer,
            "runner": self.runner,
            "refused": self.refused,
            "chunk_ids": self.chunk_ids,
            "citations": self.citations,
            "cache_hit": self.cache_hit,
            "cache_source": self.cache_source,
            "ms": self.ms,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "cost": round(self.cost, 8),
            "llm_calls": self.llm_calls,
            "spans": [s.as_dict() for s in self.spans],
            "config": self.config,
            "error": self.error,
        }


def current_config(runner: str = "agent") -> dict:
    """Everything needed to reproduce a request, captured at request time.

    Captured here rather than read back at report time. Week 6 learned that one
    painfully: a config read when the report was written stamped old answers
    with the new settings, and the run claimed a provenance it did not have.
    """
    from config import STRATEGY_STRUCTURED, get_settings
    from evals.w5_trace import corpus_fingerprint, prompt_fingerprint

    settings = get_settings()
    return {
        "runner": runner,
        "model": settings.openrouter_model,
        "temperature": settings.llm_temperature,
        "prompt_sha": prompt_fingerprint(),
        "corpus_sha": corpus_fingerprint(),
        "strategy": STRATEGY_STRUCTURED,
        "retrieval_mode": settings.retrieval_mode,
        "k": settings.eval_k,
    }


def replay_config(trace: dict) -> dict:
    """What a trace was produced under, and whether that still holds today.

    A complaint about last week is only actionable if you know whether the
    thing complained about still exists. `drifted` names every setting that has
    moved since, so "we already fixed that" is a check rather than a hope.
    """
    then = trace.get("config") or {}
    now = current_config(then.get("runner", "agent"))
    drifted = {k: (then.get(k), now.get(k)) for k in now if then.get(k) != now.get(k)}
    return {"then": then, "now": now, "drifted": drifted, "reproducible": not drifted}
