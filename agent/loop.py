"""The agent loop. Plan, act, look at the result, repeat until done.

THE WHOLE LOOP IS `run()` BELOW, AND IT IS ABOUT FIFTY LINES
    Ask the model what to do next. Run that one tool. Put the result in memory.
    Ask again. Stop when it calls finish, or when a budget runs out. There is
    nothing else. Every agent framework is this, with plugins.

WHY REACT, AND WHY THOUGHT IS NOT DECORATION
    Each turn the model writes a thought before its action. The thought is not
    for the reader. A model that has to say why it is choosing a tool picks a
    better tool, and when it picks a bad one the thought is the only place you
    can see the reasoning that led there. It is the debugging surface.

WHY JSON AND NOT FUNCTION CALLING
    Function calling is a provider feature. Parsing one JSON object works on
    every model including the free ones this project runs on, and it keeps the
    protocol visible in this file rather than inside an SDK.

WHY A PARSE FAILURE IS A TURN, NOT A CRASH
    When the reply is not valid JSON the model is told so and gets another go,
    inside the same budget. Weak models emit prose around their JSON constantly.
    A loop that dies on the first malformed reply measures the parser, not the
    agent.

WHAT THIS LOOP DELIBERATELY DOES NOT DO
    No parallel tool calls, no sub-agents, no planner-executor split, no
    reflection pass. Each of those is a real technique and each would be a
    second variable in a week whose whole point is one comparison.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field

from agent import tools
from agent.budget import (
    CALL_LIMIT,
    ERROR,
    EXHAUSTED,
    FINISHED,
    REPEAT_LIMIT,
    Budget,
)
from agent.memory import Memory, Step
from config import STRATEGY_STRUCTURED

# Bumped whenever the loop's protocol or its prompts change, because both move
# the output. run_race.py puts this in the cache key, so a cached run produced
# by an older loop stops matching instead of being quietly reused.
#
# v1  first build.
# v2  a repeated action is warned once before it stops the run, and the
#     out-of-budget answer now goes through the real grounding prompt instead
#     of a short wrap-up that the model answered without any citations.
# v3  an empty reply from the provider no longer costs a step, and the prompt
#     says outright that native tool-call tags are thrown away. Both came from
#     a live run that spent 2 of its 6 steps on replies it could not parse.
AGENT_PROMPT_VERSION = "v3"

SYSTEM = """You are a support-desk agent working a customer ticket against a help-centre corpus.

You work in a loop. Each turn you write one thought and choose ONE tool. You see
the result, then choose again. You keep going until you have the facts for every
part of the ticket, then you call finish.

TOOLS
{catalogue}

HOW TO WORK
1. Read the ticket and notice how many separate things it asks. A ticket can
   ask two or three unrelated things at once. Each one needs its own lookup.
2. Handle ONE thing per turn. Never put two questions in a single query.
3. When you see an error code, look it up by code. It is exact.
4. After each result, ask yourself what is still unanswered, and go get it.
5. Call finish only when every part of the ticket is covered, or when the
   corpus clearly does not hold a part of it.

THE FINAL ANSWER
Every sentence must end with the [chunk_id] it came from, exactly as shown in
the results. Only cite ids you have actually seen. State only what the corpus
says. If the corpus does not hold part of the ticket, say that plainly for that
part and still answer the parts it does hold.

REPLY FORMAT
Reply with one JSON object and nothing else:

{{"thought": "<one short line: what is still missing and why this tool>",
  "tool": "<tool name>",
  "args": {{"<arg>": "<value>"}}}}

No markdown, no code fence, no text before or after the JSON. Do not use
<tool_call> tags or any other tool-calling syntax. This loop reads JSON only,
and anything else is thrown away and costs you a turn."""

USER = """TICKET
{ticket}

{history}
What is your next step?"""

_HISTORY_HEADER = "WHAT YOU HAVE DONE SO FAR\n{scratchpad}\n"


@dataclass
class AgentRun:
    """One ticket, worked end to end. Shaped so the Week 6 checks can score it.

    `answer`, `refused`, `retrieved` and `citations` exist because
    evals/w6_checks.py reads those exact attributes. Scoring the agent with the
    same rules as the fixed workflow is the only way the race is fair, so the
    agent bends to the scorer rather than the scorer bending to the agent.
    """

    question: str
    answer: str = ""
    refused: bool = False
    retrieved: list[dict] = field(default_factory=list)
    citations: list = field(default_factory=list)
    gate_fired: bool = False
    budget_degraded: bool = False

    # Week 7 additions, for the race.
    runner: str = "agent"
    steps: list[Step] = field(default_factory=list)
    stop_reason: str = FINISHED
    llm_calls: int = 0
    elapsed_s: float = 0.0
    error: str | None = None

    @property
    def completed(self) -> bool:
        """Did the loop end because it was done, rather than because it ran out?"""
        return self.stop_reason == FINISHED


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse(reply: str) -> dict:
    """Pull one action object out of the reply, tolerating fences and chatter.

    Retries with strict=False because a raw newline inside a JSON string is
    invalid JSON and models emit one every single time they write a refusal,
    which is two lines by design. Rejecting those would burn a step on every
    refusal ticket and would be measuring the parser, not the agent.
    """
    match = _JSON_RE.search(reply or "")
    if not match:
        raise ValueError("no JSON object in the reply")
    blob = match.group(0)
    try:
        data = json.loads(blob)
    except json.JSONDecodeError:
        data = json.loads(blob, strict=False)
    tool = data.get("tool")
    if not isinstance(tool, str) or not tool:
        raise ValueError("no 'tool' field")
    args = data.get("args") or {}
    if not isinstance(args, dict):
        raise ValueError("'args' is not an object")
    return {"thought": str(data.get("thought", ""))[:200], "tool": tool, "args": args}


def _decide(ticket: str, memory: Memory, budget: Budget) -> tuple[dict | None, str]:
    """One LLM turn. Returns the parsed action, or None plus the raw reply."""
    from rag.answerer import _llm, invoke_with_retry

    history = _HISTORY_HEADER.format(scratchpad=memory.scratchpad()) if memory.steps else ""
    budget.spend_call()
    reply = invoke_with_retry(
        _llm(max_tokens=400),
        [
            ("system", SYSTEM.format(catalogue=tools.catalogue())),
            ("human", USER.format(ticket=ticket, history=history)),
        ],
    )
    raw = (reply.content or "").strip()
    try:
        return _parse(raw), raw
    except (ValueError, json.JSONDecodeError):
        return None, raw


# ---------------------------------------------------------------------------
# The loop
# ---------------------------------------------------------------------------
def run(ticket: str, *, budget: Budget | None = None, verbose: bool = False) -> AgentRun:
    """Work one ticket. Every step is recorded, and every exit is a named reason."""
    budget = budget or Budget()
    memory = Memory()
    result = AgentRun(question=ticket)
    started = time.monotonic()
    warned = 0  # how many times it has been told it is repeating itself

    while True:
        limit = budget.exceeded()
        if limit:
            result.stop_reason = limit
            break

        budget.spend_step()
        try:
            action, raw = _decide(ticket, memory, budget)
        except Exception as exc:
            result.stop_reason = ERROR
            result.error = f"{type(exc).__name__}: {exc}"[:300]
            break

        if action is None and not raw:
            # The provider returned nothing at all. That is not a decision the
            # model made, so it does not cost a step, only the call it already
            # spent. The call limit still bounds it, so this cannot spin.
            budget.steps -= 1
            if verbose:
                print("  (empty reply from the provider, retrying)")
            continue

        if action is None:
            # Not valid JSON. Tell the model, and let it spend another step.
            memory.add(
                Step(
                    n=budget.steps,
                    thought="",
                    tool="(unparsed)",
                    args={},
                    observation=(
                        "Your last reply was not a single JSON object, so nothing ran. "
                        'Reply with exactly {"thought": "...", "tool": "...", "args": {...}} '
                        f"and nothing else. You sent: {raw[:200]}"
                    ),
                    ok=False,
                ),
                [],
            )
            if verbose:
                print(f"  step {budget.steps}: unparsed reply")
            continue

        if budget.note_action(action["tool"], action["args"]):
            # A repeat is a warning first, a stop second. The first live run hit
            # this with both lookups already done: the model repeated instead of
            # calling finish, and killing it there threw away a run that was
            # otherwise complete. Telling it once costs a step and usually gets
            # a finish. A second repeat anywhere in the run is genuinely stuck,
            # and that does stop.
            warned += 1
            if warned >= 2:
                result.stop_reason = REPEAT_LIMIT
                break
            memory.add(
                Step(
                    n=budget.steps,
                    thought=action["thought"],
                    tool="(repeated)",
                    args=action["args"],
                    observation=(
                        "You just ran that exact call. Running it again returns the same "
                        "thing. Either look up something you have NOT looked up yet, or, "
                        "if you already have the facts for every part of the ticket, call "
                        "finish now."
                    ),
                    ok=False,
                ),
                [],
            )
            if verbose:
                print(f"  step {budget.steps}: repeated action, warned")
            continue

        outcome = tools.execute(action["tool"], action["args"])
        step = Step(
            n=budget.steps,
            thought=action["thought"],
            tool=action["tool"],
            args=action["args"],
            observation=outcome.observation,
            ok=outcome.ok,
        )
        memory.add(step, outcome.chunks)
        if verbose:
            print(f"  step {step.n}: {step.action_line()}  -> {len(outcome.chunks)} chunk(s)")

        if action["tool"] == "finish":
            result.answer = outcome.observation
            result.stop_reason = FINISHED
            break

    # A run that ran out of budget still has to produce something. It answers
    # from what it gathered rather than returning nothing, and stop_reason says
    # it was cut short, so no report can mistake it for a completed run.
    if result.stop_reason in EXHAUSTED and not result.answer:
        result.answer = _forced_answer(ticket, memory, budget)

    result.steps = memory.steps
    result.retrieved = memory.chunks
    result.llm_calls = budget.llm_calls
    result.elapsed_s = round(time.monotonic() - started, 2)
    _finalise(result)
    return result


def _forced_answer(ticket: str, memory: Memory, budget: Budget) -> str:
    """One last call to turn a cut-short run into a usable answer.

    This reuses the SAME grounding prompt the fixed workflow uses, rather than
    a short wrap-up written for this path. The first version did write its own,
    and the model dropped every citation, because a three-line instruction does
    not hold against a prompt that took Week 6 to tune. A cut-short run must
    still obey the citation rules or the loop has a hole in it where the
    grounding used to be.

    Reusing it also keeps the race fair. Both runners end up answering under
    the same rules, so a difference between them is about the loop, not about
    which prompt each one happened to get.
    """
    if not memory.seen:
        return (
            "REFUSED: The help-centre corpus does not contain this information.\n"
            "Missing: nothing was retrieved before the run hit its limit."
        )
    try:
        from rag.answerer import SYSTEM_PROMPT, USER_TEMPLATE, _llm, invoke_with_retry

        budget.spend_call()
        reply = invoke_with_retry(
            _llm(max_tokens=400),
            [
                ("system", SYSTEM_PROMPT),
                (
                    "human",
                    USER_TEMPLATE.format(
                        context=memory.context_blocks(), question=ticket
                    ),
                ),
            ],
        )
        return (reply.content or "").strip()
    except Exception as exc:
        return (
            "REFUSED: The help-centre corpus does not contain this information.\n"
            f"Missing: the run stopped early ({type(exc).__name__})."
        )


def _finalise(result: AgentRun) -> None:
    """Resolve citations and set `refused`, the same way the fixed path does."""
    from rag.answerer import REFUSAL_TOKEN, verify_citations

    context_ids = {chunk["chunk_id"] for chunk in result.retrieved}
    result.citations = verify_citations(result.answer, STRATEGY_STRUCTURED, context_ids)
    # startswith, not `in`, because that is exactly how answer_question decides
    # it. A race where the two runners are scored by different rules is not a
    # race.
    result.refused = result.answer.upper().startswith(REFUSAL_TOKEN)
