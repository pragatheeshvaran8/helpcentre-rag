"""Stop conditions. The part that keeps a loop from being a liability.

WHY THIS IS A SEPARATE FILE
    A loop with an LLM deciding when to exit has no natural end. If the model
    never calls finish, the loop runs until the money does. Four independent
    limits are enforced here, and the loop cannot run without them.

THE FOUR LIMITS
    steps     How many times round the loop. The blunt one.
    llm_calls Cost. One call per step normally, but a retry also counts.
    seconds   Wall clock, so a hanging provider cannot pin the run open.
    repeats   The same tool with the same arguments twice in a row.

WHY REPEATS ARE A STOP CONDITION AND NOT A WARNING
    A model that searches the same phrase twice has stopped making progress. It
    is not thinking, it is stuck, and the next ten steps will be the same
    search. Catching it costs nothing and is the difference between a run that
    ends at step 3 and one that ends at the step cap having learned nothing.

WHY EXHAUSTION IS NOT A CRASH
    Hitting a limit is an ordinary outcome, recorded as `stop_reason`. The run
    still returns whatever the agent gathered. A harness that crashed on the
    limit would throw away the work and teach nothing about where the loop got
    stuck.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

# Defaults. Six steps is enough for a three-part ticket with one wasted search,
# and small enough that a stuck run is cheap.
MAX_STEPS = 6
MAX_LLM_CALLS = 8
MAX_SECONDS = 120.0

# Stop reasons, as written into the run record.
FINISHED = "finished"
STEP_LIMIT = "step_limit"
CALL_LIMIT = "llm_call_limit"
TIME_LIMIT = "time_limit"
REPEAT_LIMIT = "repeated_action"
ERROR = "error"

EXHAUSTED = (STEP_LIMIT, CALL_LIMIT, TIME_LIMIT, REPEAT_LIMIT)


@dataclass
class Budget:
    """Every limit in one object, so no caller can forget one."""

    max_steps: int = MAX_STEPS
    max_llm_calls: int = MAX_LLM_CALLS
    max_seconds: float = MAX_SECONDS

    steps: int = 0
    llm_calls: int = 0
    started: float = field(default_factory=time.monotonic)
    _last_action: tuple[str, str] | None = None

    @property
    def elapsed(self) -> float:
        return time.monotonic() - self.started

    def spend_call(self) -> None:
        self.llm_calls += 1

    def spend_step(self) -> None:
        self.steps += 1

    def exceeded(self) -> str | None:
        """The limit that has been hit, or None while there is room left."""
        if self.steps >= self.max_steps:
            return STEP_LIMIT
        if self.llm_calls >= self.max_llm_calls:
            return CALL_LIMIT
        if self.elapsed >= self.max_seconds:
            return TIME_LIMIT
        return None

    def note_action(self, tool: str, args: dict) -> bool:
        """Record an action. True when it repeats the one before it.

        Compared on the rendered arguments rather than the dict, so
        `{"query": "vat"}` and `{"query": "vat"}` count as the same action even
        when the model re-emits them in a different order.
        """
        signature = (tool, repr(sorted((args or {}).items())))
        repeated = signature == self._last_action
        self._last_action = signature
        return repeated

    def as_dict(self) -> dict:
        return {
            "steps": self.steps,
            "llm_calls": self.llm_calls,
            "elapsed_s": round(self.elapsed, 2),
            "max_steps": self.max_steps,
            "max_llm_calls": self.max_llm_calls,
            "max_seconds": self.max_seconds,
        }
