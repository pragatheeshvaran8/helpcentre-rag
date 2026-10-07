"""Judge the whole path, not just the final answer.

WHY THE OUTCOME IS NOT ENOUGH
    Week 7 scored twelve tickets on what the agent said. T11 scored a clean
    pass: expected behaviour "refuse", the answer began with REFUSED, no
    failure modes. Here is the answer it passed on:

        REFUSED: The help-centre corpus does not contain this information.
        Missing: the run stopped early (RateLimitError).

    That is a crash report wearing the shape of a refusal. The agent never
    decided the corpus lacked an answer. It searched five times, ran out of
    steps, and the fallback call died on a rate limit. The error handler
    produced a string that starts with the refusal token, and every
    outcome-only check waved it through.

    A right answer reached by a wrong path is not a right answer. It is a
    coincidence that will stop happening.

WHAT THIS FILE MEASURES
    EXPECTED SEQUENCE   Which tools SHOULD this ticket need, and how many?
    TOOL CHOICE         Did it reach for the exact lookup when it had a code?
    LOOPING             Did it ask the same thing again in different words?
    WASTED STEPS        Did a step contribute nothing to the final answer?
    QUIET GIVE-UP       Did it stop and dress the stopping up as an answer?
    COST                Calls per task, mean and p99.

WHY LOOP DETECTION IS NOT THE WEEK 7 REPEAT GUARD
    The Week 7 guard compares one action to the one immediately before it,
    exactly. Both looping runs slipped past it:

        T11 step 6 repeats step 2 word for word, four steps later.
        T12 step 5 repeats step 3 word for word, two steps later.

    And neither would have caught "P1 incident SLA" against "P1 incident SLA
    response time", which is the same search with two words added. A guard that
    only sees adjacent exact matches does not see a loop. It sees six different
    queries.

WHY THIS RUNS ON SAVED TRACES
    Every metric here reads the Week 7 run records. Nothing calls a model, so
    the whole trajectory layer is free to compute, free to re-run, and free to
    change after the expensive part is already done.
"""
from __future__ import annotations

import re
import statistics
from dataclasses import dataclass, field

from agent.budget import similar_query

# Tools, by name, so a typo does not silently become a new category.
LOOKUP = "lookup_error_code"
SEARCH = "search_help_centre"
FINISH = "finish"

# Failure modes. These are about the PATH. The Week 6 modes are about the
# answer, and the two sets are deliberately kept apart: a run can be clean on
# one and broken on the other, and that gap is the point of this week.
LOOPED = "looped"
WRONG_TOOL = "wrong_tool"
WASTED_STEP = "wasted_step"
QUIET_GIVE_UP = "quiet_give_up"
NEVER_FINISHED = "never_finished"
UNPARSED_STEP = "unparsed_step"

TRAJECTORY_MODES = (
    LOOPED,
    WRONG_TOOL,
    WASTED_STEP,
    QUIET_GIVE_UP,
    NEVER_FINISHED,
    UNPARSED_STEP,
)

# ---------------------------------------------------------------------------
# What a good path looks like, per ticket
# ---------------------------------------------------------------------------
# One tool call per part of the ticket, then finish. The tool is decided by the
# shape of that part: a literal error code is an exact lookup, anything
# described in words is a search.
#
# Written here rather than in w7_tickets.py on purpose. Week 7 asked whether
# the answer was right. Week 8 asks whether the route was right. Keeping the
# expected path in this file means the Week 7 measurement cannot be quietly
# re-cut to match it.
EXPECTED_TOOLS: dict[str, list[str]] = {
    "T01": [LOOKUP, LOOKUP],            # ERR-4032, ERR-7215
    "T02": [LOOKUP, LOOKUP],            # ERR-5108, ERR-6203
    "T03": [SEARCH, SEARCH],            # dunning stage, webhook retries
    "T04": [LOOKUP, SEARCH],            # MIG-220, then the sunset policy
    "T05": [LOOKUP, LOOKUP, SEARCH],    # ERR-7208, ERR-5199, the voiding rule
    "T06": [SEARCH, LOOKUP],            # downgrade credit rule, ERR-6250
    "T07": [LOOKUP],
    "T08": [LOOKUP],
    "T09": [LOOKUP],
    "T10": [LOOKUP],
    "T11": [SEARCH],                    # not in the corpus, one look is enough
    "T12": [SEARCH],                    # only the Stripe part is asked
}

_CHUNK_RE = re.compile(r"\[((?:HC-\d{4})-(?:baseline|structured)-\d{3})\]")

# An answer whose Missing: line names one of these is not a refusal. It is the
# machinery failing and saying so in the refusal's clothes.
_GIVE_UP_MARKERS = (
    "stopped early",
    "ran out",
    "rate limit",
    "ratelimit",
    "nothing was retrieved",
    "run hit its limit",
    "budget",
    "error",
)


# The loop detector and the loop guard MUST use one definition of "the same
# question". If the detector were stricter than the guard, the fix would look
# like it worked while the agent kept looping under a slightly different rule.
# So this is imported from the guard rather than written twice.
_similar = similar_query


def _query_of(step: dict) -> str:
    args = step.get("args") or {}
    return str(args.get("query") or args.get("code") or "")


@dataclass
class Trajectory:
    """One run, judged on how it got there rather than where it got to."""

    ticket_id: str
    shape: str
    steps: int
    llm_calls: int
    seconds: float
    stop_reason: str

    expected_tools: list[str] = field(default_factory=list)
    actual_tools: list[str] = field(default_factory=list)
    tool_choice_hits: int = 0
    tool_choice_total: int = 0

    loop_pairs: list[tuple[int, int]] = field(default_factory=list)
    wasted_steps: list[int] = field(default_factory=list)
    unparsed_steps: list[int] = field(default_factory=list)
    modes: list[str] = field(default_factory=list)

    outcome_passed: bool = False

    @property
    def clean(self) -> bool:
        return not self.modes

    @property
    def tool_choice_rate(self) -> float:
        if not self.tool_choice_total:
            return 0.0
        return round(self.tool_choice_hits / self.tool_choice_total, 4)

    @property
    def extra_steps(self) -> int:
        """Steps beyond the ideal path. The ideal is one call per part, plus finish."""
        return max(0, self.steps - (len(self.expected_tools) + 1))

    @property
    def gap(self) -> bool:
        """Right answer, wrong path. The thing this week exists to find."""
        return self.outcome_passed and not self.clean

    def as_dict(self) -> dict:
        return {
            "ticket_id": self.ticket_id,
            "shape": self.shape,
            "steps": self.steps,
            "llm_calls": self.llm_calls,
            "seconds": self.seconds,
            "stop_reason": self.stop_reason,
            "expected_tools": self.expected_tools,
            "actual_tools": self.actual_tools,
            "tool_choice_rate": self.tool_choice_rate,
            "extra_steps": self.extra_steps,
            "loop_pairs": self.loop_pairs,
            "wasted_steps": self.wasted_steps,
            "unparsed_steps": self.unparsed_steps,
            "modes": self.modes,
            "outcome_passed": self.outcome_passed,
            "trajectory_clean": self.clean,
            "gap": self.gap,
        }


def _tool_choice(expected: list[str], actual: list[str]) -> tuple[int, int]:
    """How much of the ideal tool mix did it actually use?

    Compared as a multiset, not a sequence. Looking up two codes in either
    order is the same route, and scoring order would punish a correct run for
    an arbitrary choice.
    """
    remaining = list(expected)
    hits = 0
    for tool in actual:
        if tool in remaining:
            remaining.remove(tool)
            hits += 1
    return hits, len(expected)


def _find_loops(steps: list[dict]) -> list[tuple[int, int]]:
    """Every pair of steps that asked the same question, adjacent or not."""
    pairs = []
    calls = [s for s in steps if s.get("tool") in (LOOKUP, SEARCH)]
    for i, earlier in enumerate(calls):
        for later in calls[i + 1 :]:
            if earlier.get("tool") != later.get("tool"):
                continue
            if _similar(_query_of(earlier), _query_of(later)):
                pairs.append((earlier["n"], later["n"]))
    return pairs


def _find_wasted(steps: list[dict], citations: list) -> list[int]:
    """Steps whose results never reached the answer.

    A step is wasted when it surfaced chunk ids and the final answer cited none
    of them. A step that surfaced nothing at all is not counted here: that is a
    miss, not waste, and it is already visible as a loop or an extra step.
    """
    cited = {getattr(c, "chunk_id", None) or c.get("chunk_id") for c in citations}
    wasted = []
    for step in steps:
        if step.get("tool") not in (LOOKUP, SEARCH):
            continue
        found = set(_CHUNK_RE.findall(step.get("observation") or ""))
        if found and not (found & cited):
            wasted.append(step["n"])
    return wasted


def looks_like_quiet_give_up(answer: str) -> bool:
    """A refusal that is really the machinery reporting its own failure.

    The Week 6 checks ask whether the text starts with REFUSED. That is the
    right question for a model that chose to refuse and the wrong question for
    a string assembled by an exception handler. This reads the Missing: line
    and asks what it blames. A real refusal blames the corpus. This one blames
    the run.
    """
    text = (answer or "").strip()
    if not text.upper().startswith("REFUSED"):
        return False
    missing = ""
    for line in text.splitlines():
        if line.lower().startswith("missing:"):
            missing = line.lower()
            break
    if not missing:
        return False
    return any(marker in missing for marker in _GIVE_UP_MARKERS)


def evaluate(ticket: dict, run, outcome_passed: bool) -> Trajectory:
    """Score one run's path. Reads a saved record, calls no model."""
    steps = [s if isinstance(s, dict) else s.__dict__ for s in run.steps]
    traj = Trajectory(
        ticket_id=ticket["id"],
        shape=ticket["shape"],
        steps=len(steps),
        llm_calls=run.llm_calls,
        seconds=run.elapsed_s,
        stop_reason=run.stop_reason,
        expected_tools=list(EXPECTED_TOOLS.get(ticket["id"], [])),
        actual_tools=[s["tool"] for s in steps],
        outcome_passed=outcome_passed,
    )

    used = [t for t in traj.actual_tools if t in (LOOKUP, SEARCH)]
    traj.tool_choice_hits, traj.tool_choice_total = _tool_choice(traj.expected_tools, used)
    if traj.tool_choice_total and traj.tool_choice_hits < traj.tool_choice_total:
        traj.modes.append(WRONG_TOOL)

    traj.loop_pairs = _find_loops(steps)
    if traj.loop_pairs:
        traj.modes.append(LOOPED)

    traj.wasted_steps = _find_wasted(steps, run.citations)
    if traj.wasted_steps:
        traj.modes.append(WASTED_STEP)

    traj.unparsed_steps = [s["n"] for s in steps if s["tool"] in ("(unparsed)", "(repeated)")]
    if traj.unparsed_steps:
        traj.modes.append(UNPARSED_STEP)

    if looks_like_quiet_give_up(run.answer):
        traj.modes.append(QUIET_GIVE_UP)

    if run.stop_reason != "finished":
        traj.modes.append(NEVER_FINISHED)

    return traj


# ---------------------------------------------------------------------------
def summarise(trajectories: list[Trajectory]) -> dict:
    """Roll up, keeping outcome and trajectory as two separate numbers."""
    if not trajectories:
        return {"n": 0}

    calls = sorted(t.llm_calls for t in trajectories)
    n = len(trajectories)
    modes: dict[str, int] = {}
    for traj in trajectories:
        for mode in traj.modes:
            modes[mode] = modes.get(mode, 0) + 1

    return {
        "n": n,
        "outcome_passed": sum(1 for t in trajectories if t.outcome_passed),
        "trajectory_clean": sum(1 for t in trajectories if t.clean),
        "gap": sum(1 for t in trajectories if t.gap),
        "gap_ids": [t.ticket_id for t in trajectories if t.gap],
        "tool_choice_rate": round(
            sum(t.tool_choice_hits for t in trajectories)
            / max(1, sum(t.tool_choice_total for t in trajectories)),
            4,
        ),
        "perfect_route": sum(1 for t in trajectories if t.extra_steps == 0 and t.clean),
        "extra_steps_total": sum(t.extra_steps for t in trajectories),
        # Cost per task. p99 on a set this size is the worst run, and saying so
        # is more useful than printing a percentile that implies more data.
        "calls_mean": round(sum(calls) / n, 2),
        "calls_p99": calls[-1],
        "calls_p99_is_max": True,
        "calls_median": round(statistics.median(calls), 2),
        "calls_total": sum(calls),
        "modes": dict(sorted(modes.items(), key=lambda kv: (-kv[1], kv[0]))),
    }
