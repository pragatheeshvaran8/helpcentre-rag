"""The one command for Week 7. Race the agent against the fixed workflow.

    python -m evals.run_race                 both runners, every ticket
    python -m evals.run_race --runner agent  one side only
    python -m evals.run_race --ticket T01 -v watch one ticket step by step
    python -m evals.run_race --report        rescore the cache, no API calls

WHY BOTH RUNNERS ARE CACHED SEPARATELY
    Keyed by runner, ticket and the fingerprint of the prompt that produced it.
    A race that dies halfway through the free tier's daily cap resumes instead
    of starting over, and changing the agent prompt invalidates only the
    agent's half.

WHY --report EXISTS
    Running costs money, scoring does not. Every metric in this week can be
    recomputed from the cache for free, so a metric can be fixed after the
    expensive part is done without paying for the tickets again.

WHY A FAILED TICKET IS NOT A CRASH
    A provider 429 on ticket 7 of 12 leaves the other 11 on disk and the report
    says how many are missing. A partial race is marked INCOMPLETE and the
    recommendation is withheld, for the same reason Week 6 refuses to compare
    two partial runs.
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

from agent import workflow as fixed
from agent.budget import ERROR, Budget
from agent.loop import AGENT_PROMPT_VERSION
from agent.loop import run as run_agent
from config import get_settings
from evals.w5_trace import prompt_fingerprint
from evals.w7_race import AGENT, RUNNERS, WORKFLOW, recommend, score, summarise
from evals.w7_tickets import MULTI, REFUSE, SHAPES, SINGLE, ticket_set
from rag import term

RACE_DIR = "w7_race"


def _dir() -> Path:
    path = Path(get_settings().results_dir) / RACE_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _cache_path(runner: str) -> Path:
    return _dir() / f"{runner}__runs.json"


def _load(runner: str) -> dict:
    path = _cache_path(runner)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _fingerprint(runner: str) -> str:
    """What the cached answers were produced by.

    The agent's answers depend on its own loop prompt as well as the grounding
    prompt it shares with the workflow, so both go in. Change either and the
    cache stops matching, which is the point.
    """
    settings = get_settings()
    parts = [runner, settings.openrouter_model, prompt_fingerprint()]
    if runner == AGENT:
        parts.append(AGENT_PROMPT_VERSION)
    return "|".join(parts)


def _serialise(result) -> dict:
    return {
        "question": result.question,
        "answer": result.answer,
        "refused": result.refused,
        "retrieved": result.retrieved,
        "citations": [
            {
                "chunk_id": c.chunk_id,
                "resolves": c.resolves,
                "was_in_context": c.was_in_context,
                "article_id": c.article_id,
                "source_file": c.source_file,
                "text": c.text,
            }
            for c in result.citations
        ],
        "runner": result.runner,
        "steps": [asdict(s) for s in result.steps],
        "stop_reason": result.stop_reason,
        "llm_calls": result.llm_calls,
        "elapsed_s": result.elapsed_s,
        "error": result.error,
        "gate_fired": result.gate_fired,
        "budget_degraded": result.budget_degraded,
        "fingerprint": None,  # filled by the caller
    }


class _Replayed:
    """A cached run, shaped like the live object the scorer expects."""

    class _Cite:
        def __init__(self, d: dict) -> None:
            self.chunk_id = d["chunk_id"]
            self.resolves = d["resolves"]
            self.was_in_context = d.get("was_in_context", True)
            self.article_id = d.get("article_id")
            self.source_file = d.get("source_file")
            self.text = d.get("text")

    class _Step:
        def __init__(self, d: dict) -> None:
            self.__dict__.update(d)

    def __init__(self, d: dict) -> None:
        self.question = d["question"]
        self.answer = d["answer"]
        self.refused = d["refused"]
        self.retrieved = d.get("retrieved", [])
        self.citations = [self._Cite(c) for c in d.get("citations", [])]
        self.runner = d["runner"]
        self.steps = [self._Step(s) for s in d.get("steps", [])]
        self.stop_reason = d.get("stop_reason", "finished")
        self.llm_calls = d.get("llm_calls", 0)
        self.elapsed_s = d.get("elapsed_s", 0.0)
        self.error = d.get("error")
        self.gate_fired = d.get("gate_fired", False)
        self.budget_degraded = d.get("budget_degraded", False)

    @property
    def completed(self) -> bool:
        return self.stop_reason == "finished"


# ---------------------------------------------------------------------------
def race(runner: str, tickets: list[dict], *, refresh: bool, verbose: bool) -> dict:
    """Run one side of the race, reusing anything already on disk."""
    cache = {} if refresh else _load(runner)
    path = _cache_path(runner)
    want = _fingerprint(runner)

    for ticket in tickets:
        hit = cache.get(ticket["id"])
        if hit is not None and hit.get("fingerprint") == want:
            if verbose:
                print(term.grey(f"  {ticket['id']}  cached"))
            continue

        print(f"  {ticket['id']}  {term.dim(ticket['question'][:58])}")
        started = time.monotonic()
        try:
            if runner == AGENT:
                result = run_agent(ticket["question"], budget=Budget(), verbose=verbose)
            else:
                result = fixed.run(ticket["question"], verbose=verbose)
        except Exception as exc:
            print(term.red(f"       failed: {str(exc)[:80]}"))
            continue

        if result.stop_reason == ERROR:
            # A provider failure is not a result. Caching it would mean a 429 on
            # one ticket permanently froze that ticket as failed, and the whole
            # point of the cache is that an outage costs time and not work.
            # Budget exhaustion IS cached: that is the agent really running out.
            print(term.red(f"       {result.error[:90] if result.error else 'error'}"))
            print(term.grey("       not cached, so it retries next run"))
            continue

        record = _serialise(result)
        record["fingerprint"] = want
        cache[ticket["id"]] = record
        path.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding="utf-8")
        print(
            term.grey(
                f"       {result.stop_reason}  {len(result.steps)} step(s)  "
                f"{result.llm_calls} call(s)  {time.monotonic() - started:.1f}s"
            )
        )
    return cache


def score_all(tickets: list[dict], caches: dict) -> dict:
    """Rescore every cached run. Free, and safe to repeat.

    A record whose fingerprint no longer matches is treated as missing, not as
    a result. It was produced by a different prompt or an older loop, and
    reporting it beside current runs would be the same quiet restamping that
    Week 6 had to go back and fix once already. Counting it missing makes the
    race read INCOMPLETE until it is re-run, which is the honest state.
    """
    out = {}
    for runner in RUNNERS:
        cache = caches.get(runner, {})
        want = _fingerprint(runner)
        scores, stale = [], []
        for ticket in tickets:
            record = cache.get(ticket["id"])
            if record is None:
                continue
            if record.get("fingerprint") != want:
                stale.append(ticket["id"])
                continue
            scores.append(score(ticket, _Replayed(record)))
        current = {s.ticket_id for s in scores}
        out[runner] = {
            "scores": scores,
            "summary": summarise(scores),
            "missing": [t["id"] for t in tickets if t["id"] not in current],
            "stale": stale,
        }
    return out


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def write_report(tickets: list[dict], scored: dict, path: Path) -> None:
    # Refuse to replace a finished report with an empty one.
    #
    # The staleness guard treats a record made by an older loop as missing, on
    # purpose. Week 8 changed the loop, so every Week 7 record went stale at
    # once, and the next --report wrote a file whose every row said "not run".
    # The guard was right. Overwriting the finished report with the result was
    # not: that file is the record of what happened in Week 7, and changing the
    # agent afterwards does not change what Week 7 measured.
    # EITHER side being empty is enough. Week 8 bumped the agent loop version,
    # so all twelve agent records went stale while the workflow's stayed valid.
    # A first version checked that BOTH sides were empty and happily wrote a
    # report whose every agent row read "not run".
    one_side_empty = not scored[AGENT]["scores"] or not scored[WORKFLOW]["scores"]
    if one_side_empty and path.exists():
        print(term.yellow("Every cached run is stale, so there is nothing to score."))
        print(term.yellow(f"Leaving {path.name} as it is rather than blanking it."))
        print(term.grey("Re-run the race to produce a current report."))
        return

    a, w = scored[AGENT], scored[WORKFLOW]
    agent_sum, work_sum = a["summary"], w["summary"]
    complete = not a["missing"] and not w["missing"]

    lines = [
        "# Week 7: agent against fixed workflow",
        "",
        f"- Tickets: {len(tickets)}  "
        f"({sum(1 for t in tickets if t['shape'] == MULTI)} multi-part, "
        f"{sum(1 for t in tickets if t['shape'] == SINGLE)} single, "
        f"{sum(1 for t in tickets if t['shape'] == REFUSE)} not in corpus)",
        f"- Model: `{get_settings().openrouter_model}`",
        f"- Grounding prompt: `{prompt_fingerprint()}`   agent loop prompt: "
        f"`{AGENT_PROMPT_VERSION}`",
        "",
    ]

    if not complete:
        lines += [
            "> **INCOMPLETE RACE.** Not every ticket ran, so the totals below cover",
            "> different sets of tickets for the two runners and the recommendation",
            "> is withheld.",
            f"> Missing for agent: {', '.join(a['missing']) or 'none'}",
            f"> Missing for workflow: {', '.join(w['missing']) or 'none'}",
            "",
        ]
        stale = (a.get("stale") or []) + (w.get("stale") or [])
        if stale:
            lines += [
                f"> {len(stale)} cached run(s) were produced by an older prompt or loop",
                "> and are not scored here. Re-run to replace them.",
                "",
            ]

    if agent_sum.get("n") and work_sum.get("n"):
        lines += [
            "## Speed, cost, reliability",
            "",
            "| | agent | fixed workflow |",
            "|---|---|---|",
            f"| Tickets scored | {agent_sum['n']} | {work_sum['n']} |",
            f"| **Speed** median s/ticket | {agent_sum['median_seconds']} | "
            f"{work_sum['median_seconds']} |",
            f"| Slowest ticket | {agent_sum['slowest_seconds']}s | "
            f"{work_sum['slowest_seconds']}s |",
            f"| **Cost** LLM calls total | {agent_sum['llm_calls']} | {work_sum['llm_calls']} |",
            f"| Calls per ticket | {agent_sum['calls_per_ticket']} | "
            f"{work_sum['calls_per_ticket']} |",
            f"| **Reliability** passed | {agent_sum['passed']}/{agent_sum['n']} | "
            f"{work_sum['passed']}/{work_sum['n']} |",
            f"| Ran to completion | {agent_sum['completed']}/{agent_sum['n']} | "
            f"{work_sum['completed']}/{work_sum['n']} |",
            f"| Errors | {agent_sum['errors']} | {work_sum['errors']} |",
            "",
            "## Did it answer the whole ticket?",
            "",
            "A two-part ticket with one part answered is not half right. It is wrong.",
            "",
            "| | agent | fixed workflow |",
            "|---|---|---|",
            f"| Parts cited, all tickets | {agent_sum['parts_cited_rate']:.0%} | "
            f"{work_sum['parts_cited_rate']:.0%} |",
            f"| Parts cited, multi-part only | {agent_sum['multi_parts_cited_rate']:.0%} | "
            f"{work_sum['multi_parts_cited_rate']:.0%} |",
            f"| Multi-part tickets fully answered | "
            f"{agent_sum['multi_fully_cited']}/{agent_sum['multi_n']} | "
            f"{work_sum['multi_fully_cited']}/{work_sum['multi_n']} |",
            "",
            "## By ticket shape",
            "",
            "| Shape | agent passed | workflow passed | agent calls | workflow calls |",
            "|---|---|---|---|---|",
        ]
        for shape in SHAPES:
            ar = agent_sum["by_shape"].get(shape, {})
            wr = work_sum["by_shape"].get(shape, {})
            lines.append(
                f"| {shape} | {ar.get('passed', 0)}/{ar.get('n', 0)} "
                f"| {wr.get('passed', 0)}/{wr.get('n', 0)} "
                f"| {ar.get('llm_calls', 0)} | {wr.get('llm_calls', 0)} |"
            )

        lines += [
            "",
            "## Why the agent stopped",
            "",
            "| Reason | agent | workflow |",
            "|---|---|---|",
        ]
        for reason in sorted(set(agent_sum["stop_reasons"]) | set(work_sum["stop_reasons"])):
            lines.append(
                f"| {reason} | {agent_sum['stop_reasons'].get(reason, 0)} "
                f"| {work_sum['stop_reasons'].get(reason, 0)} |"
            )

        lines += ["", "## Per ticket", "", "| Ticket | shape | runner | pass | parts cited | steps | calls | s |", "|---|---|---|---|---|---|---|---|"]
        for ticket in tickets:
            for runner in RUNNERS:
                row = next(
                    (s for s in scored[runner]["scores"] if s.ticket_id == ticket["id"]), None
                )
                if row is None:
                    lines.append(f"| {ticket['id']} | {ticket['shape']} | {runner} | not run | | | | |")
                    continue
                lines.append(
                    f"| {row.ticket_id} | {row.shape} | {row.runner} "
                    f"| {'yes' if row.passed else 'no'} "
                    f"| {row.coverage.cited}/{row.coverage.total} "
                    f"| {row.steps} | {row.llm_calls} | {row.seconds} |"
                )

        if complete:
            verdict = recommend(agent_sum, work_sum)
            lines += [
                "",
                "## Which one would I ship",
                "",
                f"**{verdict.ship}.**",
                "",
                verdict.reason,
                "",
                "| Ticket shape | better runner |",
                "|---|---|",
            ]
            for shape, winner in verdict.per_shape.items():
                lines.append(f"| {shape} | {winner} |")
            lines += [
                "",
                "The rule that picked this is written in `evals/w7_race.py` and was",
                "written before the race ran. Coverage of multi-part tickets decides",
                "it, cost breaks ties, and a gap smaller than one whole ticket counts",
                "as no gap on a set this size.",
            ]
        else:
            lines += [
                "",
                "## Which one would I ship",
                "",
                "Withheld. The race did not finish, and a recommendation from a",
                "partial race is a guess with a table attached.",
            ]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_steps(tickets: list[dict], caches: dict, path: Path) -> None:
    """Every step of every agent run, so the loop is visible and checkable."""
    lines = [
        "# Week 7: the agent's steps, in full",
        "",
        "Every turn of the loop for every ticket. This is the file to read when",
        "an answer looks wrong: the thought line says why the tool was chosen.",
        "",
    ]
    cache = caches.get(AGENT, {})
    for ticket in tickets:
        record = cache.get(ticket["id"])
        lines += [f"## {ticket['id']}  ({ticket['shape']}, {ticket['parts']} part(s))", ""]
        lines += [f"> {ticket['question']}", ""]
        if record is None:
            lines += ["_not run_", ""]
            continue
        lines.append(
            f"Stopped: **{record['stop_reason']}** after {len(record['steps'])} step(s), "
            f"{record['llm_calls']} LLM call(s), {record['elapsed_s']}s."
        )
        lines.append("")
        for step in record["steps"]:
            args = ", ".join(f"{k}={v!r}" for k, v in (step.get("args") or {}).items())
            lines.append(f"**Step {step['n']}** `{step['tool']}({args})`")
            if step.get("thought"):
                lines.append(f"- thought: {step['thought']}")
            observation = " ".join((step.get("observation") or "").split())
            lines.append(f"- result: {observation[:400]}")
            lines.append("")
        lines += ["**Final answer**", "", "```", record["answer"].strip() or "(empty)", "```", ""]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
def main() -> None:
    term.init()
    parser = argparse.ArgumentParser(description="Week 7: agent vs fixed workflow.")
    parser.add_argument("--runner", choices=RUNNERS, help="Run one side only.")
    parser.add_argument("--ticket", help="Run one ticket by id, e.g. T01.")
    parser.add_argument("--report", action="store_true", help="Rescore the cache. No API calls.")
    parser.add_argument("--refresh", action="store_true", help="Ignore the cache and re-run.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print every step live.")
    args = parser.parse_args()

    tickets = ticket_set()
    if args.ticket:
        tickets = [t for t in tickets if t["id"] == args.ticket.upper()]
        if not tickets:
            parser.error(f"No ticket {args.ticket!r}.")

    runners = [args.runner] if args.runner else list(RUNNERS)
    caches = {}

    if not args.report:
        for runner in runners:
            print(term.rule(f"{runner}  ({len(tickets)} ticket(s))"))
            caches[runner] = race(
                runner, tickets, refresh=args.refresh, verbose=args.verbose
            )
            print()

    for runner in RUNNERS:
        caches.setdefault(runner, _load(runner))

    all_tickets = ticket_set()
    scored = score_all(all_tickets, caches)

    out = Path(get_settings().results_dir)
    write_report(all_tickets, scored, out / "w7_race.md")
    write_steps(all_tickets, caches, out / "w7_agent_steps.md")
    # Same protection as the report: do not replace a finished scores file with
    # one that has an empty side.
    if scored[AGENT]["scores"] and scored[WORKFLOW]["scores"]:
        payload = {
            runner: {
                "summary": scored[runner]["summary"],
                "scores": [s.as_dict() for s in scored[runner]["scores"]],
            }
            for runner in RUNNERS
        }
        (_dir() / "scores.json").write_text(
            json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    a, w = scored[AGENT]["summary"], scored[WORKFLOW]["summary"]
    print(term.rule("result"))
    if not a.get("n") and not w.get("n"):
        print(term.yellow("Nothing has run yet. Try: python -m evals.run_race"))
    elif not a.get("n") or not w.get("n"):
        # One side only. Say which side is missing rather than implying nothing
        # ran, which is what the first version did after `--runner agent`.
        ran, missing = (AGENT, WORKFLOW) if a.get("n") else (WORKFLOW, AGENT)
        done = a if ran == AGENT else w
        print(f"  {ran}: {done['passed']}/{done['n']} passed, {done['llm_calls']} LLM call(s)")
        print()
        print(term.yellow(f"No {missing} runs yet, so there is nothing to race against."))
        print(term.grey(f"  python -m evals.run_race --runner {missing}"))
    else:
        print(f"  {'':22} {'agent':>10} {'workflow':>10}")
        print(f"  {'passed':22} {a['passed']}/{a['n']:<8} {w['passed']}/{w['n']:<8}")
        print(f"  {'median seconds':22} {a['median_seconds']:>10} {w['median_seconds']:>10}")
        print(f"  {'LLM calls':22} {a['llm_calls']:>10} {w['llm_calls']:>10}")
        print(
            f"  {'multi fully answered':22} "
            f"{a['multi_fully_cited']}/{a['multi_n']:<8} {w['multi_fully_cited']}/{w['multi_n']:<8}"
        )
        missing = scored[AGENT]["missing"] + scored[WORKFLOW]["missing"]
        if missing:
            print()
            print(term.yellow(f"INCOMPLETE: {len(missing)} run(s) missing. Recommendation withheld."))
        else:
            print()
            print(term.bold(f"  ship: {recommend(a, w).ship}"))
    print()
    print(f"Wrote {out / 'w7_race.md'}")
    print(f"Wrote {out / 'w7_agent_steps.md'}")


if __name__ == "__main__":
    main()
