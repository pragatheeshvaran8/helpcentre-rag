"""A manager and two specialists, to race against the single agent.

THE TOPOLOGY
    MANAGER     reads the ticket, splits it into parts, hands each part to one
                specialist, then writes the final answer from what comes back.
    CODE DESK   one specialist. Error codes only. Exact lookups.
    POLICY DESK one specialist. Anything described in words.

    That is the orchestrator-worker pattern, and the split is the natural one
    for a support queue: a code is a key lookup, a policy question is a search.

WHY THIS COSTS MORE THAN IT LOOKS
    A hand-off is not one extra call. It is the WHOLE CONTEXT, again.

    The single agent sends the ticket once and keeps everything in one growing
    conversation. The squad sends the ticket to the manager, then again to each
    specialist with its own instructions, then the specialists' findings go
    back into the manager's final prompt. The same ticket text is paid for
    three or four times, and every specialist carries its own system prompt
    that the single agent never needed.

    `agent/meter.py` counts that, per participant, so the claim is a number
    rather than an opinion.

A2A, AND WHAT IS ACTUALLY IMPLEMENTED
    A2A is the standard for one agent handing work to another, the way MCP is
    the standard for an agent reaching a tool. Two of its ideas are built here
    because they are what make a hand-off legible:

      AGENT CARD      each specialist publishes what it is for and what it can
                      do. The manager routes by reading cards, not by a
                      hard-coded if-statement. Swap a card and the routing
                      changes with no manager edit.

      TASK LIFECYCLE  every hand-off is a Task with a state: submitted,
                      working, then completed or failed. A specialist that
                      fails fails its own task, and the manager carries on with
                      the rest.

    What is NOT built: the A2A wire protocol, its JSON-RPC envelope, discovery
    over HTTP, or streaming. These agents are in one process. Building the
    transport would add a second variable to a week whose whole point is one
    measurement, and the concepts above are the part that changes the design.

WHAT IS HELD IDENTICAL TO THE SINGLE AGENT
    Same model, same temperature, same corpus, same tools over the same MCP
    servers, same tickets, same scoring. Only the topology differs. Anything
    else and the race would be measuring two changes at once.
"""
from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field

from agent.meter import Meter, metered_invoke
from agent.toolbox import Toolbox

# Task states, as A2A names them.
SUBMITTED = "submitted"
WORKING = "working"
COMPLETED = "completed"
FAILED = "failed"


@dataclass
class AgentCard:
    """What a specialist publishes about itself.

    The manager routes by reading these. Nothing in the manager's code names a
    specialist, so changing the team means changing this list, which is the
    same trick Week 9 played with tool discovery.
    """

    name: str
    title: str
    description: str
    skills: list[str]
    tools: list[str]
    instructions: str

    def summary(self) -> str:
        """The card as the manager reads it."""
        return (
            f"{self.name}  ({self.title})\n"
            f"    {self.description}\n"
            f"    good at: {', '.join(self.skills)}"
        )


@dataclass
class Task:
    """One unit of work handed to one specialist."""

    task_id: str
    assignee: str
    instruction: str
    state: str = SUBMITTED
    result: str = ""
    error: str | None = None
    steps: list[dict] = field(default_factory=list)
    chunks: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "assignee": self.assignee,
            "instruction": self.instruction,
            "state": self.state,
            "result": self.result[:600],
            "error": self.error,
            "tool_calls": [s["tool"] for s in self.steps],
        }


# ---------------------------------------------------------------------------
# The cards
# ---------------------------------------------------------------------------
CODE_DESK = AgentCard(
    name="code_desk",
    title="error-code specialist",
    description=(
        "Looks up a single error code and reports its cause and documented fix, "
        "word for word from the help centre."
    ),
    skills=["error codes", "ERR-nnnn", "MIG-nnn", "what a code means", "the documented fix"],
    tools=["lookup_error_code"],
    instructions=(
        "You handle ONE error code. Look it up with lookup_error_code, then "
        "report its cause and its fix exactly as the help centre states them. "
        "Every sentence must end with the [chunk_id] it came from. If the code "
        "is not in the corpus, say so in one line and stop. Do not look up "
        "anything you were not asked about."
    ),
)

POLICY_DESK = AgentCard(
    name="policy_desk",
    title="policy and symptom specialist",
    description=(
        "Answers anything described in words: what an agent is allowed to do, "
        "what a symptom means, why something changed, what the history shows."
    ),
    skills=["policy", "what am I allowed to do", "symptoms with no code",
            "procedures", "account history", "why something changed"],
    tools=["search_help_centre", "get_ticket_history", "find_similar_tickets"],
    instructions=(
        "You handle ONE question described in words. Search for it, then answer "
        "from what you find. Every sentence must end with the [chunk_id] it "
        "came from, when the source has one. If the corpus does not hold it, "
        "say so in one line and stop. Do not answer anything you were not "
        "asked about."
    ),
)

SQUAD = [CODE_DESK, POLICY_DESK]
CARDS = {c.name: c for c in SQUAD}


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------
MANAGER_SPLIT = """You are the manager of a small support desk. You do not answer tickets
yourself. You split them and hand each part to the right specialist.

YOUR TEAM
{cards}

HOW TO SPLIT
1. Read the ticket and count the separate things it asks. Most ask one. Some
   ask two or three.
2. Give each part to ONE specialist, chosen by what their card says they are
   good at.
3. Write each instruction as a complete, standalone question. The specialist
   cannot see the ticket, only what you write.
4. Never give one specialist two questions. Split them instead.
5. If a part fits no specialist, do not invent one. Leave it out.

REPLY FORMAT
Reply with one JSON object and nothing else:

{{"parts": [{{"assignee": "<specialist name>", "instruction": "<one standalone question>"}}]}}

No markdown, no code fence, no text before or after the JSON."""

MANAGER_ASSEMBLE = """You are the manager of a support desk. Your specialists have reported back.
Write the reply the agent will send.

RULES
1. Use ONLY what your specialists reported. You did no research yourself and
   have no other knowledge.
2. Keep every [chunk_id] exactly as the specialist wrote it. Those are the
   citations, and a claim without one cannot be checked.
3. Cover every part of the ticket your specialists answered.
4. If a specialist reported that something is not in the corpus, say that
   plainly for that part, and still answer the parts that were answered.
5. If NO specialist found anything, reply with exactly:

REFUSED: The help-centre corpus does not contain this information.
Missing: <one short line naming what was asked for and not found>

Write the reply and nothing else. No preamble, no sign-off."""

SPECIALIST = """You are the {title} on a support desk.

{instructions}

TOOLS
{catalogue}

Work in a loop. Each turn, write one thought and choose ONE tool. You will see
the result, then choose again. Call finish as soon as you have the answer to
the ONE question you were given.

REPLY FORMAT
Reply with one JSON object and nothing else:

{{"thought": "<one short line>", "tool": "<tool name>", "args": {{"<arg>": "<value>"}}}}

No markdown, no code fence, no text before or after the JSON. Do not use
<tool_call> tags or any other tool-calling syntax."""


@dataclass
class SquadRun:
    """One ticket, worked by the team. Same shape the Week 6 checks read."""

    question: str
    answer: str = ""
    refused: bool = False
    retrieved: list[dict] = field(default_factory=list)
    citations: list = field(default_factory=list)
    gate_fired: bool = False
    budget_degraded: bool = False

    runner: str = "squad"
    steps: list = field(default_factory=list)
    stop_reason: str = COMPLETED
    llm_calls: int = 0
    elapsed_s: float = 0.0
    error: str | None = None

    tasks: list[Task] = field(default_factory=list)
    meter: Meter = field(default_factory=Meter)

    @property
    def completed(self) -> bool:
        return self.stop_reason == COMPLETED


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_json(reply: str) -> dict:
    match = _JSON_RE.search(reply or "")
    if not match:
        raise ValueError("no JSON object in the reply")
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return json.loads(match.group(0), strict=False)


# ---------------------------------------------------------------------------
# The specialists
# ---------------------------------------------------------------------------
# A specialist is a small agent loop: it sees only its own instruction, only
# its own tools, and it stops as soon as it has answered the one thing it was
# given. Narrow on purpose. A specialist that could do everything would just be
# the single agent with a longer prompt.
SPECIALIST_MAX_STEPS = 3


def _run_specialist(
    card: AgentCard, task: Task, toolbox: Toolbox, meter: Meter, *, verbose: bool
) -> Task:
    """One specialist works one task. A failure fails the task, not the run."""
    from agent.loop import _parse
    from rag.answerer import _llm

    task.state = WORKING
    allowed = [n for n in toolbox.names() if n in card.tools or n == "finish"]
    catalogue = "\n\n".join(
        f"{n}({toolbox.tools[n].arg_line()})\n    {toolbox.tools[n].description}"
        for n in allowed
    )
    system = SPECIALIST.format(
        title=card.title, instructions=card.instructions, catalogue=catalogue
    )

    history = ""
    for step in range(1, SPECIALIST_MAX_STEPS + 1):
        user = f"YOUR QUESTION\n{task.instruction}\n\n{history}What is your next step?"
        try:
            reply = metered_invoke(
                _llm(max_tokens=400),
                [("system", system), ("human", user)],
                meter,
                card.name,
                f"step {step}",
            )
            action = _parse((reply.content or "").strip())
        except Exception as exc:
            task.state = FAILED
            task.error = f"{type(exc).__name__}: {exc}"[:160]
            return task

        chosen = action["tool"]
        if chosen not in allowed:
            # A specialist reaching for someone else's tool is told so and gets
            # another turn, inside its own small budget.
            history += (
                f"Step {step}\n  you asked for: {chosen}\n"
                f"  result: that tool is not yours. Yours are: {', '.join(allowed)}.\n\n"
            )
            continue

        if chosen == "finish":
            task.result = str(action["args"].get("answer") or "")
            task.state = COMPLETED
            task.steps.append({"tool": "finish", "args": action["args"]})
            if verbose:
                print(f"      {card.name}: finished in {step} step(s)")
            return task

        outcome = toolbox.execute(chosen, action["args"])
        task.steps.append({"tool": chosen, "args": action["args"]})
        task.chunks.extend(outcome.chunks)
        history += (
            f"Step {step}\n  thought: {action['thought']}\n"
            f"  action: {chosen}({action['args']})\n"
            f"  result: {outcome.observation}\n\n"
        )
        if verbose:
            print(f"      {card.name}: {chosen} -> {len(outcome.chunks)} chunk(s)")

    # Out of steps with no finish. Whatever it saw is still worth returning: the
    # manager can use a partial finding, and a silent failure cannot.
    task.result = task.result or _last_observation(history)
    if task.result:
        task.state = COMPLETED
    else:
        task.state = FAILED
        task.error = "no answer within the step limit"
    return task


def _last_observation(history: str) -> str:
    """The final tool result, for a specialist that ran out of steps."""
    marker = "  result: "
    if marker not in history:
        return ""
    return history.rsplit(marker, 1)[1].strip()[:1200]


# ---------------------------------------------------------------------------
# The manager
# ---------------------------------------------------------------------------
def run(
    ticket: str,
    *,
    toolbox: Toolbox,
    verbose: bool = False,
    max_parts: int = 4,
) -> SquadRun:
    """Work one ticket with the team. Split, hand off, assemble.

    `toolbox` is required rather than built here, so the race can hand both
    runners the same one. Starting a second set of MCP servers for the squad
    would charge it for a start-up the single agent did not pay.
    """
    from config import STRATEGY_STRUCTURED
    from rag.answerer import REFUSAL_TOKEN, _llm, verify_citations

    result = SquadRun(question=ticket)
    meter = result.meter
    started = time.monotonic()

    # -- 1. the manager splits the ticket --------------------------------
    cards = "\n\n".join(c.summary() for c in SQUAD)
    try:
        reply = metered_invoke(
            _llm(max_tokens=400),
            [("system", MANAGER_SPLIT.format(cards=cards)), ("human", f"TICKET\n{ticket}")],
            meter,
            "manager",
            "split",
        )
        parts = _parse_json((reply.content or "").strip()).get("parts") or []
    except Exception as exc:
        result.stop_reason = FAILED
        result.error = f"split failed: {type(exc).__name__}: {exc}"[:200]
        result.elapsed_s = round(time.monotonic() - started, 2)
        result.llm_calls = meter.n_calls
        return result

    if verbose:
        print(f"    manager split into {len(parts)} part(s)")

    # -- 2. hand each part to a specialist -------------------------------
    for i, part in enumerate(parts[:max_parts], start=1):
        assignee = str(part.get("assignee") or "").strip()
        instruction = str(part.get("instruction") or "").strip()
        task = Task(task_id=f"t{i}", assignee=assignee, instruction=instruction)
        result.tasks.append(task)

        card = CARDS.get(assignee)
        if card is None or not instruction:
            task.state = FAILED
            task.error = f"no specialist named {assignee!r}"
            if verbose:
                print(f"      unroutable: {assignee!r}")
            continue

        if verbose:
            print(f"      -> {assignee}: {instruction[:62]}")
        _run_specialist(card, task, toolbox, meter, verbose=verbose)
        result.retrieved.extend(task.chunks)

    done = [t for t in result.tasks if t.state == COMPLETED and t.result]

    # -- 3. the manager assembles ----------------------------------------
    if not done:
        result.answer = (
            f"{REFUSAL_TOKEN}: The help-centre corpus does not contain this information.\n"
            "Missing: no specialist could answer any part of this ticket."
        )
        result.stop_reason = COMPLETED if result.tasks else FAILED
    else:
        reports = "\n\n".join(
            f"--- {t.assignee} was asked: {t.instruction}\n{t.result}" for t in done
        )
        unanswered = [t for t in result.tasks if t not in done]
        if unanswered:
            reports += "\n\n--- not answered:\n" + "\n".join(
                f"{t.assignee}: {t.instruction} ({t.error or t.state})" for t in unanswered
            )
        try:
            reply = metered_invoke(
                _llm(max_tokens=500),
                [
                    ("system", MANAGER_ASSEMBLE),
                    (
                        "human",
                        f"THE TICKET\n{ticket}\n\nWHAT YOUR SPECIALISTS REPORTED\n{reports}",
                    ),
                ],
                meter,
                "manager",
                "assemble",
            )
            result.answer = (reply.content or "").strip()
        except Exception as exc:
            result.stop_reason = FAILED
            result.error = f"assemble failed: {type(exc).__name__}: {exc}"[:200]

    # -- 4. finish like every other runner -------------------------------
    # De-duplicate: two specialists may have surfaced the same chunk, and
    # counting it twice would flatter the squad's retrieval.
    seen, unique = set(), []
    for chunk in result.retrieved:
        if chunk["chunk_id"] not in seen:
            seen.add(chunk["chunk_id"])
            unique.append(chunk)
    result.retrieved = unique

    result.citations = verify_citations(result.answer, STRATEGY_STRUCTURED, seen)
    result.refused = result.answer.upper().startswith(REFUSAL_TOKEN)
    result.llm_calls = meter.n_calls
    result.elapsed_s = round(time.monotonic() - started, 2)
    result.steps = [
        {"n": i, "tool": s["tool"], "args": s["args"], "who": t.assignee}
        for i, (t, s) in enumerate(
            ((t, s) for t in result.tasks for s in t.steps), start=1
        )
    ]
    return result
