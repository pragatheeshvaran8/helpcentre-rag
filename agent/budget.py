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

import re
import time
from dataclasses import dataclass, field

# Two queries that are the same question in different words. Jaccard overlap:
# shared words over all words used.
#
# 0.5 was measured, not guessed. Across the twelve Week 7 runs:
#
#   Healthy runs peak at 0.33. The highest pair anywhere is "ERR-4032" against
#   "ERR-7215", two different codes that share the word "err".
#   Looping runs start at 0.50 and reach 1.00, where a query is repeated word
#   for word several steps later.
#
# So there is clear air between 0.33 and 0.50, and the threshold sits in it.
# At 0.5 every loop pair in T11 and T12 is caught, twelve of them, and no pair
# in any healthy run is touched. A first guess of 0.7 missed seven of those
# twelve, including "P1 incident SLA" against "P1 incident SLA response time".
#
# This lives here, beside the guard that enforces it, and evals/w8_trajectory.py
# imports it rather than defining its own. The thing that MEASURES looping and
# the thing that PREVENTS it have to agree, or the before-and-after number is
# measuring two different definitions.
SIMILARITY = 0.5
_WORD_RE = re.compile(r"[a-z0-9]+")


def similar_query(a: str, b: str) -> bool:
    """Is this the same question asked again in different words?"""
    wa = set(_WORD_RE.findall((a or "").lower()))
    wb = set(_WORD_RE.findall((b or "").lower()))
    if not wa or not wb:
        return False
    return len(wa & wb) / len(wa | wb) >= SIMILARITY

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

    # Week 8 fix. When True, an action counts as repeated if it asks the same
    # question as ANY earlier action, not just the one immediately before it.
    #
    # The Week 7 guard compared adjacent actions, exactly. Both looping runs
    # walked straight past it. T11 repeated step 2 at step 6, four steps later.
    # T12 repeated step 3 at step 5. Neither was adjacent, and neither was
    # caught, so both burned seven calls and hit the step limit.
    #
    # Set False to reproduce the Week 7 behaviour, which is how the
    # before-and-after number is produced with one variable changed.
    similar_guard: bool = True

    steps: int = 0
    llm_calls: int = 0
    started: float = field(default_factory=time.monotonic)
    _last_action: tuple[str, str] | None = None
    _history: list[tuple[str, str]] = field(default_factory=list)

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
        """Record an action. True when it asks something already asked.

        Compared on the rendered arguments rather than the dict, so
        `{"query": "vat"}` and `{"query": "vat"}` count as the same action even
        when the model re-emits them in a different order.

        With `similar_guard` on, the comparison also runs against every earlier
        action of the same tool, by meaning rather than by exact text. An agent
        that rewords the same search is not making progress, and the number of
        steps between the two attempts does not change that.
        """
        signature = (tool, repr(sorted((args or {}).items())))
        query = str((args or {}).get("query") or (args or {}).get("code") or "")

        repeated = signature == self._last_action
        if not repeated and self.similar_guard:
            repeated = any(
                past_tool == tool and similar_query(past_query, query)
                for past_tool, past_query in self._history
            )

        self._last_action = signature
        self._history.append((tool, query))
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
