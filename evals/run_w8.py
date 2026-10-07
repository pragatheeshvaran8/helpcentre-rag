"""The one command for Week 8.

    python -m evals.run_w8 --trajectory   score the saved paths. Free.
    python -m evals.run_w8 --attack       run the injection suite, both ways.
    python -m evals.run_w8 --fix          re-run the tickets with the loop fix.
    python -m evals.run_w8 --report       rebuild every report from cache. Free.

WHY WEEK 7's CACHE IS NEVER WRITTEN
    The loop changed, so every Week 7 record is now stale against it. Re-running
    them into results/w7_race/ would overwrite the evidence that Week 7's report
    is built on. Week 8 keeps its own cache in results/w8_runs/ and reads Week 7
    without ever writing to it.

THE THREE THINGS THIS WEEK HAS TO SHOW
    1. A case where the answer was right and the path was wrong.
    2. An attack that works, and then does not.
    3. A before-and-after number on the top failure.
"""
from __future__ import annotations

import argparse
import json
import statistics
from dataclasses import asdict
from pathlib import Path

from agent import guard
from agent.budget import ERROR, Budget
from agent.loop import AGENT_PROMPT_VERSION
from agent.loop import run as run_agent
from config import get_settings
from evals.run_race import _Replayed
from evals.w7_race import score
from evals.w7_tickets import TICKETS_BY_ID, ticket_set
from evals.w8_injection import ATTACKS, MARKER, counts as attack_counts
from evals.w8_trajectory import evaluate, summarise
from rag import term

W8_DIR = "w8_runs"
W7_AGENT_CACHE = "w7_race/agent__runs.json"


def _dir() -> Path:
    path = Path(get_settings().results_dir) / W8_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load(name: str) -> dict:
    path = _dir() / f"{name}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save(name: str, data: dict) -> None:
    (_dir() / f"{name}.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


def _w7_runs() -> dict:
    path = Path(get_settings().results_dir) / W7_AGENT_CACHE
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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
        "guarded": result.guarded,
        "injection_hits": result.injection_hits,
        "output_blocked": result.output_blocked,
        "block_reasons": result.block_reasons,
    }


# ---------------------------------------------------------------------------
# 1. Trajectory: the gap
# ---------------------------------------------------------------------------
def trajectories(runs: dict) -> list:
    out = []
    for ticket in ticket_set():
        record = runs.get(ticket["id"])
        if not record:
            continue
        run = _Replayed(record)
        out.append(evaluate(ticket, run, score(ticket, run).passed))
    return out


# ---------------------------------------------------------------------------
# 2. Attacks
# ---------------------------------------------------------------------------
def _poison(attack, original_execute):
    """Make one tool return a document carrying the payload.

    The corpus on disk is untouched. This is what the model would see if a
    help-centre article had been edited by an attacker, which is the realistic
    version of the threat: nobody needs access to the agent, only to a document
    the agent reads.
    """

    def patched(name, args):
        outcome = original_execute(name, args)
        if outcome.chunks:
            outcome.observation = outcome.observation + attack.payload
        return outcome

    return patched


def run_attacks(*, guarded: bool, verbose: bool) -> dict:
    """Run every attack, with the defences on or off."""
    from agent import tools

    label = "defended" if guarded else "undefended"
    cache = _load(f"attacks_{label}")
    original = tools.execute
    results = cache

    for attack in ATTACKS:
        if attack.id in cache:
            if verbose:
                print(term.grey(f"  {attack.id}  cached"))
            continue

        ticket = TICKETS_BY_ID[attack.ticket]
        question = ticket["question"]
        if attack.channel == "ticket":
            question = question + attack.payload

        print(f"  {attack.id}  {attack.kind:8} {attack.goal:18} on {attack.ticket}")
        try:
            if attack.channel == "tool_output":
                tools.execute = _poison(attack, original)
            run = run_agent(
                question,
                budget=Budget(max_steps=4),
                verbose=verbose,
                guarded=guarded,
                output_markers=(MARKER,),
            )
        except Exception as exc:
            print(term.red(f"       failed: {str(exc)[:80]}"))
            continue
        finally:
            tools.execute = original

        if run.stop_reason == ERROR:
            print(term.red(f"       {(run.error or '')[:80]}"))
            print(term.grey("       not cached, retries next run"))
            continue

        landed = attack.succeeded(run.answer)
        record = _serialise(run)
        record["attack_id"] = attack.id
        record["attack_landed"] = landed
        results[attack.id] = record
        _save(f"attacks_{label}", results)

        verdict = term.red("ATTACK LANDED") if landed else term.green("blocked")
        extra = ""
        if run.injection_hits:
            extra += f"  stripped={len(run.injection_hits)}"
        if run.output_blocked:
            extra += "  output-blocked"
        print(f"       {verdict}{extra}")

    return results


# ---------------------------------------------------------------------------
# 3. The fix, measured
# ---------------------------------------------------------------------------
def run_tickets(*, similar_guard: bool, verbose: bool) -> dict:
    """Re-run the twelve tickets with the loop guard on or off."""
    label = "fixed" if similar_guard else "unfixed"
    cache = _load(f"tickets_{label}")

    for ticket in ticket_set():
        if ticket["id"] in cache:
            if verbose:
                print(term.grey(f"  {ticket['id']}  cached"))
            continue
        print(f"  {ticket['id']}  {term.dim(ticket['question'][:54])}")
        try:
            run = run_agent(
                ticket["question"],
                budget=Budget(similar_guard=similar_guard),
                verbose=verbose,
                guarded=True,
            )
        except Exception as exc:
            print(term.red(f"       failed: {str(exc)[:80]}"))
            continue
        if run.stop_reason == ERROR:
            print(term.red(f"       {(run.error or '')[:80]}"))
            print(term.grey("       not cached, retries next run"))
            continue
        cache[ticket["id"]] = _serialise(run)
        _save(f"tickets_{label}", cache)
        print(
            term.grey(
                f"       {run.stop_reason}  {len(run.steps)} step(s)  "
                f"{run.llm_calls} call(s)  {run.elapsed_s}s"
            )
        )
    return cache


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------
def write_trajectory_report(trajs: list, path: Path) -> None:
    s = summarise(trajs)
    lines = [
        "# Week 8: the outcome-vs-trajectory gap",
        "",
        "Scored over the twelve Week 7 agent runs. Nothing here calls a model.",
        "",
        "## The gap",
        "",
        "| | count |",
        "|---|---|",
        f"| Tickets | {s['n']} |",
        f"| **Outcome** passed | **{s['outcome_passed']}/{s['n']}** |",
        f"| **Trajectory** clean | **{s['trajectory_clean']}/{s['n']}** |",
        f"| **Right answer, wrong path** | **{s['gap']}** |",
        "",
        f"The gap is on {', '.join(s['gap_ids']) or 'no tickets'}.",
        "",
        "Outcome-only scoring gives a perfect card. It is wrong about two of",
        "the twelve, and it is wrong in the direction that matters: those two",
        "look fine and will not stay fine.",
        "",
        "## Cost per task",
        "",
        "| | calls |",
        "|---|---|",
        f"| mean | {s['calls_mean']} |",
        f"| median | {s['calls_median']} |",
        f"| p99 | {s['calls_p99']} |",
        f"| total | {s['calls_total']} |",
        "",
        "p99 on twelve runs is the worst run. Saying so is more useful than a",
        "percentile that implies more data than exists.",
        "",
        "## Tool choice",
        "",
        f"Tool-choice accuracy is **{s['tool_choice_rate']:.0%}**. The agent picks the",
        "right tool every time. Picking the tool is not the problem. Knowing",
        "when to stop is.",
        "",
        f"Perfect route, no wasted steps: **{s['perfect_route']}/{s['n']}**. ",
        f"Extra steps beyond the ideal path: **{s['extra_steps_total']}**.",
        "",
        "## Failure modes on the path",
        "",
        "| Mode | count |",
        "|---|---|",
    ]
    for mode, count in s["modes"].items():
        lines.append(f"| `{mode}` | {count} |")

    lines += ["", "## Per ticket", "",
              "| Ticket | shape | outcome | path | tool choice | extra steps | modes |",
              "|---|---|---|---|---|---|---|"]
    for t in trajs:
        lines.append(
            f"| {t.ticket_id} | {t.shape} | {'pass' if t.outcome_passed else 'fail'} "
            f"| {'clean' if t.clean else '**broken**'} | {t.tool_choice_rate:.0%} "
            f"| {t.extra_steps} | {', '.join(t.modes) or '-'} |"
        )

    lines += ["", "## The loops, step by step", ""]
    for t in trajs:
        if t.loop_pairs:
            pairs = ", ".join(f"step {a} = step {b}" for a, b in t.loop_pairs)
            lines.append(f"- **{t.ticket_id}**: {pairs}")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_attack_report(undef: dict, defended: dict, path: Path) -> None:
    n = attack_counts()
    lines = [
        "# Week 8: prompt injection, attacked and defended",
        "",
        f"- Attacks: {n['total']} ({n['indirect']} indirect, {n['direct']} direct)",
        f"- Marker the payloads ask for: `{MARKER}`",
        "",
        "Indirect means the payload arrives inside a retrieved document. The",
        "attacker never talks to the agent. They write into something it reads.",
        "",
        "## Did it land?",
        "",
        "| Attack | kind | goal | ticket | undefended | defended |",
        "|---|---|---|---|---|---|",
    ]
    for a in ATTACKS:
        u = undef.get(a.id)
        d = defended.get(a.id)
        u_cell = "not run" if u is None else ("**LANDED**" if u["attack_landed"] else "blocked")
        d_cell = "not run" if d is None else ("**LANDED**" if d["attack_landed"] else "blocked")
        lines.append(f"| {a.id} | {a.kind} | {a.goal} | {a.ticket} | {u_cell} | {d_cell} |")

    u_land = sum(1 for r in undef.values() if r["attack_landed"])
    d_land = sum(1 for r in defended.values() if r["attack_landed"])
    lines += [
        "",
        "## Headline",
        "",
        "| | undefended | defended |",
        "|---|---|---|",
        f"| Attacks run | {len(undef)} | {len(defended)} |",
        f"| **Landed** | **{u_land}** | **{d_land}** |",
        "",
        "## What each attack was",
        "",
    ]
    for a in ATTACKS:
        lines += [f"**{a.id}** ({a.kind}, {a.goal}) on {a.ticket}", "", f"> {a.note}", ""]

    lines += [
        "## What still gets through",
        "",
        "- The scanner is a pattern list. A payload phrased differently is not",
        "  matched. It buys time, not safety.",
        "- Output validation only knows the goals it was given. An attack aiming",
        "  at something nobody enumerated passes it.",
        "- Neither layer reads intent. Both are filters in front of a problem",
        "  that is not solved.",
        "- The real containment here is least privilege, not these filters. The",
        "  tools read one local corpus. No write, no shell, no network, no",
        "  secrets. A fully successful injection can make the agent say",
        "  something wrong. It cannot make it do anything.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_fix_report(before: list, after: list, path: Path) -> None:
    b, a = summarise(before), summarise(after)
    common = {t.ticket_id for t in before} & {t.ticket_id for t in after}
    bi = {t.ticket_id: t for t in before if t.ticket_id in common}
    ai = {t.ticket_id: t for t in after if t.ticket_id in common}

    lines = [
        "# Week 8: closing the top failure mode",
        "",
        "**The mode:** `looped`. The agent asks the same question again in",
        "different words, and the Week 7 guard does not see it because it only",
        "compares one action to the one immediately before it, exactly.",
        "",
        "**The fix:** an action now counts as repeated when it asks the same",
        "question as any earlier action, measured by word overlap.",
        "",
        "**One variable moved.** Same prompts, same tools, same tickets, same",
        "model. Only `Budget.similar_guard` changes.",
        "",
        f"Compared over the {len(common)} tickets both runs scored.",
        "",
        "## The number",
        "",
        "| | before | after |",
        "|---|---|---|",
    ]
    if common:
        pb = sum(1 for t in bi.values() if t.outcome_passed)
        pa = sum(1 for t in ai.values() if t.outcome_passed)
        cb = sum(1 for t in bi.values() if t.clean)
        ca = sum(1 for t in ai.values() if t.clean)
        gb = sum(1 for t in bi.values() if t.gap)
        ga = sum(1 for t in ai.values() if t.gap)
        lb = sum(1 for t in bi.values() if "looped" in t.modes)
        la = sum(1 for t in ai.values() if "looped" in t.modes)
        kb = sorted(t.llm_calls for t in bi.values())
        ka = sorted(t.llm_calls for t in ai.values())
        lines += [
            f"| Outcome passed | {pb}/{len(common)} | {pa}/{len(common)} |",
            f"| **Trajectory clean** | **{cb}/{len(common)}** | **{ca}/{len(common)}** |",
            f"| **Right answer, wrong path** | **{gb}** | **{ga}** |",
            f"| **Tickets that looped** | **{lb}** | **{la}** |",
            f"| Calls, mean | {round(sum(kb)/len(kb), 2)} | {round(sum(ka)/len(ka), 2)} |",
            f"| Calls, median | {statistics.median(kb)} | {statistics.median(ka)} |",
            f"| Calls, p99 (worst run) | {kb[-1]} | {ka[-1]} |",
            f"| Calls, total | {sum(kb)} | {sum(ka)} |",
            "",
            "## Per ticket",
            "",
            "| Ticket | before calls | after calls | before modes | after modes |",
            "|---|---|---|---|---|",
        ]
        for tid in sorted(common):
            lines.append(
                f"| {tid} | {bi[tid].llm_calls} | {ai[tid].llm_calls} "
                f"| {', '.join(bi[tid].modes) or '-'} | {', '.join(ai[tid].modes) or '-'} |"
            )
    else:
        lines.append("| no tickets scored in both runs | | |")

    lines += [
        "",
        "## The guard against a cheap win",
        "",
        "Stopping earlier is trivially cheaper and would be worthless if the",
        "answers got worse. Outcome pass rate is reported above for exactly",
        "that reason. A fix that cuts calls and drops answers is not a fix.",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
def main() -> None:
    term.init()
    parser = argparse.ArgumentParser(description="Week 8: trajectory, injection, one fix.")
    parser.add_argument("--trajectory", action="store_true", help="Score saved paths. Free.")
    parser.add_argument("--attack", action="store_true", help="Run the injection suite.")
    parser.add_argument("--fix", action="store_true", help="Re-run tickets, guard on and off.")
    parser.add_argument("--report", action="store_true", help="Rebuild reports from cache. Free.")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if not any((args.trajectory, args.attack, args.fix, args.report)):
        parser.error("pick one: --trajectory, --attack, --fix, or --report")

    out = Path(get_settings().results_dir)

    if args.attack:
        print(term.rule("attacks, undefended"))
        run_attacks(guarded=False, verbose=args.verbose)
        print()
        print(term.rule("attacks, defended"))
        run_attacks(guarded=True, verbose=args.verbose)
        print()

    if args.fix:
        print(term.rule("tickets, loop guard OFF (before)"))
        run_tickets(similar_guard=False, verbose=args.verbose)
        print()
        print(term.rule("tickets, loop guard ON (after)"))
        run_tickets(similar_guard=True, verbose=args.verbose)
        print()

    # Reports always rebuild from whatever is cached.
    w7 = _w7_runs()
    if w7:
        trajs = trajectories(w7)
        write_trajectory_report(trajs, out / "w8_trajectory.md")
        s = summarise(trajs)
        print(term.rule("the gap, on the Week 7 runs"))
        print(f"  outcome passed    : {s['outcome_passed']}/{s['n']}")
        print(f"  trajectory clean  : {s['trajectory_clean']}/{s['n']}")
        print(f"  {term.bold('right answer, wrong path')}: {s['gap']}  {s['gap_ids']}")
        print(f"  calls mean / p99  : {s['calls_mean']} / {s['calls_p99']}")
        print(f"  modes             : {s['modes']}")
        print()

    undef, defended = _load("attacks_undefended"), _load("attacks_defended")
    if undef or defended:
        write_attack_report(undef, defended, out / "w8_injection.md")
        print(term.rule("injection"))
        print(f"  undefended landed : {sum(1 for r in undef.values() if r['attack_landed'])}"
              f"/{len(undef)}")
        print(f"  defended landed   : {sum(1 for r in defended.values() if r['attack_landed'])}"
              f"/{len(defended)}")
        print()

    unfixed, fixed = _load("tickets_unfixed"), _load("tickets_fixed")
    if unfixed and fixed:
        before, after = trajectories(unfixed), trajectories(fixed)
        write_fix_report(before, after, out / "w8_fix.md")
        # Summarise only the tickets BOTH runs scored. The first version
        # summarised the full lists, so a 12-ticket before was printed beside an
        # 11-ticket after as "10/12 -> 9/11". That is two different case sets in
        # one row, which is exactly the denominator trap Week 6 had to fix.
        shared = {t.ticket_id for t in before} & {t.ticket_id for t in after}
        sb = summarise([t for t in before if t.ticket_id in shared])
        sa = summarise([t for t in after if t.ticket_id in shared])
        print(term.rule("the fix"))
        print(f"  trajectory clean  : {sb['trajectory_clean']}/{sb['n']} -> "
              f"{sa['trajectory_clean']}/{sa['n']}")
        print(f"  looped            : {sb['modes'].get('looped', 0)} -> "
              f"{sa['modes'].get('looped', 0)}")
        print(f"  calls mean        : {sb['calls_mean']} -> {sa['calls_mean']}")
        print(f"  outcome passed    : {sb['outcome_passed']}/{sb['n']} -> "
              f"{sa['outcome_passed']}/{sa['n']}  (guard against a cheap win)")
        print()

    print(f"agent loop version: {AGENT_PROMPT_VERSION}")


if __name__ == "__main__":
    main()
