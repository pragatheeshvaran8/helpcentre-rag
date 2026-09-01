"""Week 5 step 3: group the notes, rank the groups, pick one, predict the result.

ORDER OF WORK, WHICH MATTERS MORE THAN THE GROUPS
    1. evals/w5_collect.py   ran 20 traces and wrote them out
    2. evals/w5_notes.py     one honest sentence per trace, written while reading
    3. this file             the groups, which came out of those sentences

    Nothing here was decided before step 2. Every group name below is a rewrite
    of something a note already said, and every group points back at the traces
    it came from, so a reader can check the grouping instead of trusting it.

WHAT MAKES A GOOD GROUP NAME
    A stranger who has never seen this repo has to know what went wrong from the
    name alone. "Refuses a question the corpus can answer" passes. "Bucket C",
    "generation defect" and "hallucination-adjacent" do not.

SEVERITY IS ABOUT WHAT REACHES THE CUSTOMER
    Frequency is counted. Severity is a judgement, so the ladder is written down
    here and applied the same way to every group.

        3  The agent cannot tell a right answer from a wrong one. Wrong or
           unsourced information can reach the customer looking exactly like
           sourced information.
        2  The agent gets nothing they can act on and has to work around the
           app. Nothing wrong reaches the customer; the app's usefulness is
           what is lost.
        1  The answer is right and checkable, only clumsier to use than it
           should be.

RANK = FREQUENCY x SEVERITY
    Crude on purpose. It stops a single dramatic one-off outranking a dull
    problem that happens three times.
"""
from __future__ import annotations

import json
from pathlib import Path

from config import get_settings
from evals.w5_notes import NOTES

RESULTS = Path(get_settings().results_dir)
TRACES_PATH = RESULTS / "w5_traces.json"
MD_PATH = RESULTS / "w5_taxonomy.md"

SEVERITY_SCALE = {
    3: "The agent cannot tell a right answer from a wrong one. Wrong or unsourced "
       "information can reach the customer looking exactly like sourced information.",
    2: "The agent gets nothing they can act on and has to work around the app. "
       "Nothing wrong reaches the customer; the app's usefulness is what is lost.",
    1: "The answer is right and checkable, only clumsier to use than it should be.",
}


GROUPS: list[dict] = [
    {
        "key": "refuses_answerable",
        "name": "Refuses a question the corpus can answer",
        "traces": ["T10", "T11", "T19"],
        "severity": 2,
        "what_you_see": (
            "The app returns the fixed refusal, and the Missing line names "
            "something the corpus really does contain. In all three the "
            "answering chunk was in the context the model was shown."
        ),
        "why_we_think_it_happens": (
            "The three questions ask for a SHAPE the corpus does not have, while "
            "asking for SUBSTANCE it does have. T10 asked to be walked through a "
            "procedure and the corpus has a one-line fix. T19 asked \"can I\" and "
            "the corpus states what the agent should do instead. T11 asked about a "
            "code sitting at rank 2 behind a look-alike code. Prompt rule 5 makes "
            "a partial answer a refusal, and the model appears to read a shape "
            "mismatch as a partial answer."
        ),
        "fix_direction": (
            "One prompt change: say that a refusal is about missing FACTS, never "
            "about the question's wording, and that an answer covering the "
            "substance in fewer steps than asked for is still an answer."
        ),
    },
    {
        "key": "answer_without_citation",
        "name": "Answers with nothing you can check",
        "traces": ["T04", "T09"],
        "severity": 3,
        "what_you_see": (
            "A fluent, correct answer with no [chunk_id] anywhere in it. T09 goes "
            "further and names its source in words, \"the migration status codes "
            "table\", which looks like a citation and cannot be resolved."
        ),
        "why_we_think_it_happens": (
            "Prompt rule 1 requires a citation on every sentence and the model "
            "simply does not comply on some answers. Nothing in the app enforces "
            "it afterwards: verify_citations checks the ids that ARE present and "
            "has nothing to say about an answer with none."
        ),
        "fix_direction": (
            "Enforce it in code rather than asking again. An answer with zero "
            "resolvable citations is not an answer, and should be handled the way "
            "an unresolvable citation already is."
        ),
    },
    {
        "key": "refusal_then_answer",
        "name": "Prints a refusal, then answers anyway",
        "traces": ["T02"],
        "severity": 2,
        "what_you_see": (
            "The reply opens with the exact refusal block, continues \"Wait, let "
            "me re-read the context blocks\", and then gives the correct answer. "
            "The app reads the refusal token and reports a refusal, so the correct "
            "answer underneath is thrown away."
        ),
        "why_we_think_it_happens": (
            "Prompt rule 4 says reply with the refusal 'and nothing else'. The "
            "model treats the refusal as a first draft it may revise. The app "
            "assumes the token can only appear in a real refusal, so one "
            "self-correcting reply is enough to break the contract."
        ),
        "fix_direction": (
            "Decide the refusal on the whole reply, not the opening line. A reply "
            "that contains the refusal token AND a resolvable citation is not a "
            "refusal, and should be treated as a prompt violation to be seen, not "
            "silently converted into one."
        ),
    },
]

# When two groups score the same, this decides which one is attacked first.
TIE_BREAK = (
    "Attack the group that leaves the agent with nothing at all. A correct answer "
    "with a missing citation still carries the answer, and an agent can check it "
    "against the chunks on screen. A refusal carries nothing, and an agent refused "
    "twice stops opening the tool. That is the failure that ends the product."
)

TARGET_KEY = "refuses_answerable"

# Written BEFORE the change is made. Week 6 measures against this, whatever it says.
PREDICTION = {
    "change": (
        "One prompt change: separate 'the facts are not in the context' from 'the "
        "question is worded in a shape the corpus does not use', and allow a "
        "refusal only for the first."
    ),
    "why_it_should_work": (
        "All three failures had the answering chunk in the context. Nothing was "
        "missing except a licence to answer, so no retrieval change can move this "
        "number and a prompt change should move all of it."
    ),
    "measured_on": (
        "The whole 60-question pool, not just the 20 traces that were read. 40 of "
        "the 60 have never been run. Measuring only the traces that produced the "
        "hypothesis would be marking my own homework."
    ),
    "metrics": [
        {
            "metric": "False refusals among the 15 answerable traces read",
            "now": "3 of 15",
            "predicted": "0 or 1 of 15",
            "falsified_if": "still 3 of 15",
        },
        {
            "metric": "False refusals across all 53 answerable pool questions",
            "now": "not measured; 38 of them have never been run",
            "predicted": "under 10 percent, so 5 or fewer of 53",
            "falsified_if": "10 percent or more",
        },
        {
            "metric": "Correct refusals across all 7 pool questions that should be refused",
            "now": "5 of 5 among those read; the other 2 have never been run",
            "predicted": "6 or 7 of 7",
            "falsified_if": "5 or fewer of 7",
        },
        {
            "metric": "Answers with zero citations among the 15 answerable traces read",
            "now": "2 of 15",
            "predicted": "no worse than 2 of 15",
            "falsified_if": "3 or more of 15",
        },
    ],
    "guard": (
        "The third metric is the one that stops a cheap win. Loosening the refusal "
        "rule until nothing is ever refused would clear metrics 1 and 2 and wreck "
        "the app. If correct refusals fall, the change has failed even if false "
        "refusals go to zero."
    ),
    "confound_to_control": (
        "The generation model is a free tier and this project has already had to "
        "change model once mid-way. Before and after MUST be measured in the same "
        "session, on the same model, with the same corpus_sha. A before-number "
        "carried over from a different day is not a baseline."
    ),
}


# ---------------------------------------------------------------------------
def _load_traces() -> list[dict]:
    return json.loads(TRACES_PATH.read_text(encoding="utf-8"))


def failing_trace_ids(traces: list[dict] | None = None) -> list[str]:
    traces = traces if traces is not None else _load_traces()
    return [t["trace_id"] for t in traces if t["grading"]["outcome"] == "fail"]


def assigned_trace_ids() -> list[str]:
    out: list[str] = []
    for group in GROUPS:
        out.extend(group["traces"])
    return out


def ranking() -> list[dict]:
    """Groups ordered by frequency x severity, highest first.

    Ties are left as ties. The tie-break is a stated rule applied when the target
    is chosen, not a hidden sort key that makes the tie disappear.
    """
    scored = [
        {
            **group,
            "frequency": len(group["traces"]),
            "score": len(group["traces"]) * group["severity"],
        }
        for group in GROUPS
    ]
    return sorted(scored, key=lambda g: (-g["score"], -g["severity"], g["key"]))


def target() -> dict:
    for group in ranking():
        if group["key"] == TARGET_KEY:
            return group
    raise KeyError(f"TARGET_KEY {TARGET_KEY} is not a group")


def consistency_problems() -> list[str]:
    """Ways the taxonomy could disagree with the traces. Empty means it agrees."""
    traces = _load_traces()
    failing = set(failing_trace_ids(traces))
    assigned = assigned_trace_ids()
    problems: list[str] = []

    duplicates = {t for t in assigned if assigned.count(t) > 1}
    if duplicates:
        problems.append(f"trace in more than one group: {sorted(duplicates)}")

    unassigned = sorted(failing - set(assigned))
    if unassigned:
        problems.append(f"failing trace in no group: {unassigned}")

    invented = sorted(set(assigned) - failing)
    if invented:
        problems.append(f"grouped a trace that did not fail: {invented}")

    empty = [g["key"] for g in GROUPS if not g["traces"]]
    if empty:
        problems.append(f"group with no traces: {empty}")

    missing_notes = sorted(t for t in assigned if t not in NOTES)
    if missing_notes:
        problems.append(f"grouped a trace with no note: {missing_notes}")

    bad_severity = [g["key"] for g in GROUPS if g["severity"] not in SEVERITY_SCALE]
    if bad_severity:
        problems.append(f"severity outside the scale: {bad_severity}")

    return problems


# ---------------------------------------------------------------------------
def render() -> str:
    traces = _load_traces()
    by_id = {t["trace_id"]: t for t in traces}
    ranked = ranking()
    chosen = target()

    answerable = [t for t in traces if t["expected_behaviour"] == "answer"]
    refusal_expected = [t for t in traces if t["expected_behaviour"] == "refuse"]
    failures = [t for t in traces if t["grading"]["outcome"] == "fail"]

    out: list[str] = [
        "# Week 5 — problem taxonomy and the one thing to fix next",
        "",
        "Built from [`evals/w5_notes.py`](../evals/w5_notes.py), which was written "
        "while reading [`w5_traces.md`](w5_traces.md) and before any group existed.",
        "",
        "## The sample in one line",
        "",
        f"{len(traces)} traces read. {len(traces) - len(failures)} passed, "
        f"{len(failures)} failed. "
        f"{len(answerable)} should have been answered, {len(refusal_expected)} should "
        f"have been refused.",
        "",
        "**Retrieval was correct in every single failure.** All "
        f"{len(answerable)} answerable traces put the answering chunk inside the "
        "top 3, and 6 of them still came out wrong. The Week 4 metric scores this "
        "sample 100 percent.",
        "",
        "## How severity was judged",
        "",
        "| Severity | Meaning |",
        "|---|---|",
    ]
    for level in sorted(SEVERITY_SCALE, reverse=True):
        out.append(f"| {level} | {SEVERITY_SCALE[level]} |")

    out += [
        "",
        "## The ranking",
        "",
        "| Rank | Problem | How often | Severity | Score | Traces |",
        "|---|---|---|---|---|---|",
    ]
    for i, group in enumerate(ranked, start=1):
        marker = " **<- chosen**" if group["key"] == chosen["key"] else ""
        out.append(
            f"| {i} | {group['name']}{marker} | {group['frequency']} of {len(traces)} "
            f"| {group['severity']} | **{group['score']}** | "
            + ", ".join(group["traces"])
            + " |"
        )

    top_score = ranked[0]["score"]
    tied = [g for g in ranked if g["score"] == top_score]
    if len(tied) > 1:
        out += [
            "",
            f"**The top {len(tied)} are tied on {top_score}.** "
            + " and ".join(f"“{g['name']}”" for g in tied)
            + " score the same, and the tie is real rather than something to round "
            "away.",
            "",
            f"**Tie-break rule.** {TIE_BREAK}",
        ]

    out += ["", "---", "", "## The groups", ""]
    for group in ranked:
        out += [
            f"### {group['name']}",
            "",
            f"**Traces:** {', '.join(group['traces'])} · "
            f"**How often:** {group['frequency']} of {len(traces)} · "
            f"**Severity:** {group['severity']} · **Score:** {group['score']}",
            "",
            f"**What you see.** {group['what_you_see']}",
            "",
            f"**Why we think it happens.** {group['why_we_think_it_happens']}",
            "",
            f"**Fix direction.** {group['fix_direction']}",
            "",
            "**The notes this group came from**",
            "",
        ]
        for trace_id in group["traces"]:
            trace = by_id[trace_id]
            out.append(f"- **{trace_id}** ({trace['question_id']}, `{trace['kind']}`): {NOTES[trace_id]}")
        out += ["", "---", ""]

    out += [
        "## What is NOT a group",
        "",
        "Two things were tempting and are left out, because no trace failed on them.",
        "",
        "- **A look-alike code taking the top rank.** In T11 the vector arm put the "
        "ERR-7302 tax row first, ahead of the ERR-4032 row the question asked about. "
        "The BM25 arm pulled the right chunk to rank 2, so retrieval passed and the "
        "refusal is what failed. Worth watching, not worth fixing yet.",
        "- **Refusals on under-specified questions.** All 5 came out right, and their "
        "Missing lines named the detail an agent has to supply. Calling this a problem "
        "would mean the app is wrong for doing the thing it was built to do.",
        "",
        "---",
        "",
        f"## The target: {chosen['name']}",
        "",
        f"**The change.** {PREDICTION['change']}",
        "",
        f"**Why it should work.** {PREDICTION['why_it_should_work']}",
        "",
        f"**Where it gets measured.** {PREDICTION['measured_on']}",
        "",
        "## The prediction, written before the change",
        "",
        "| Metric | Now | Predicted after | Falsified if |",
        "|---|---|---|---|",
    ]
    for m in PREDICTION["metrics"]:
        out.append(
            f"| {m['metric']} | {m['now']} | {m['predicted']} | {m['falsified_if']} |"
        )

    out += [
        "",
        f"**The guard.** {PREDICTION['guard']}",
        "",
        f"**The confound to control.** {PREDICTION['confound_to_control']}",
        "",
    ]

    problems = consistency_problems()
    out += [
        "## Self-check",
        "",
        "| Check | Result |",
        "|---|---|",
        f"| Every failing trace is in exactly one group | {'yes' if not problems else 'NO'} |",
        f"| No passing trace was put in a group | {'yes' if not problems else 'NO'} |",
        f"| Every grouped trace has a hand-written note | {'yes' if not problems else 'NO'} |",
        "",
    ]
    if problems:
        out.append("**Problems found:**")
        out += [f"- {p}" for p in problems]
        out.append("")

    return "\n".join(out)


def main() -> None:
    problems = consistency_problems()
    for problem in problems:
        print(f"PROBLEM: {problem}")

    MD_PATH.write_text(render(), encoding="utf-8")
    print(f"wrote {MD_PATH}")

    print()
    for i, group in enumerate(ranking(), start=1):
        mark = "  <- target" if group["key"] == TARGET_KEY else ""
        print(
            f"{i}. {group['name']:<45} freq {group['frequency']} x sev "
            f"{group['severity']} = {group['score']}{mark}"
        )


if __name__ == "__main__":
    main()
