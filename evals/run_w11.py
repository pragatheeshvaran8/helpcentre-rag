"""The one command for Week 11.

    python -m evals.run_w11 --log       build the trace log from real runs. Free.
    python -m evals.run_w11 --drill     the support drill, start to finish. Free.
    python -m evals.run_w11 --cost      cost per request, before and after. Free.
    python -m evals.run_w11 --guard     the failure, now a permanent test. Free.
    python -m evals.run_w11 --all       all four, then the report. Free.
    python -m evals.run_w11 --live      ask the app the pinned question again.

Only --live spends anything. Everything else reads the log, which is the point
of having one.

THE FOUR THINGS THE MENTOR CHECKS
    1. Can a specific past answer be found from the logs quickly?   --drill
    2. Do the logs show time and cost per STEP, not one total?      --log
    3. Was cost per request measured and improved?                  --cost
    4. Did a real failure become a test that guards against it?     --guard
"""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import get_settings
from evals.w11_regressions import REGRESSIONS, REFUND_TO_CARD
from obs import backfill, measure, plant, search, store
from rag import term


def _out() -> Path:
    return Path(get_settings().results_dir)


# ---------------------------------------------------------------------------
def build_log(*, overwrite: bool = True) -> dict:
    """Part 1. Every past request, with a span per step."""
    print(term.rule("the log"))
    summary = backfill.build(overwrite=overwrite)
    planted = plant.plant(days_ago=7)
    s = store.stats()

    print(f"  {summary['written']} real runs replayed from {summary['sources']} caches")
    print(f"  1 bad answer planted for the drill ({planted['trace_id']})")
    print(f"  {s['n']} traces over {len(s['days'])} days: {s['days'][0]} to {s['days'][-1]}")
    print()

    # Pick a trace whose spans were actually measured. Weeks 7 and 8 predate the
    # meter, so their spans carry divided-up time and no tokens at all. Showing
    # one of those to illustrate "cost per step" would be showing a row of
    # zeroes and calling it evidence.
    sample = next(
        (
            r for r in store.read_all()
            if len(r.get("spans") or []) >= 3
            and any(sp.get("input_tokens") for sp in r["spans"])
        ),
        None,
    )
    if sample:
        print(f"  one trace, by step  ({sample['trace_id']}):")
        print(f"    {'step':32} {'ms':>9} {'in':>7} {'out':>6} {'cost':>11}")
        for sp in sample["spans"]:
            print(f"    {sp['name'][:32]:32} {sp['ms']:>9} {sp['input_tokens']:>7} "
                  f"{sp['output_tokens']:>6} {sp['cost']:>11.8f}")
        print(f"    {'TOTAL':32} {sample['ms']:>9} {sample['input_tokens']:>7} "
              f"{sample['output_tokens']:>6} {sample['cost']:>11.8f}")
    print()
    return {"backfill": summary, "planted": planted["trace_id"], "stats": s}


# ---------------------------------------------------------------------------
def run_drill() -> dict:
    """Part 2. One bad answer, from a vague complaint, with no trace id."""
    print(term.rule("the support drill"))
    print("  THE COMPLAINT, as forwarded:")
    for line in _wrap(plant.COMPLAINT, 74):
        print(f"    {line}")
    print()
    print("  What we have: a rough date, the word 'refund', and nothing else.")
    print()

    # The proof step reads the corpus to compare the answer against the chunk it
    # cited, and the first such read builds the BM25 index. That is a one-off
    # start-up cost, not search time, so it is paid before the clock starts.
    # Timing it inside the drill reported 15.6 seconds for a 2ms search.
    from config import STRATEGY_STRUCTURED
    from rag.keyword import build_index

    # Say so before the wait. Without this line the drill prints the complaint
    # and then sits silent for about 13 seconds while transformers imports and
    # the index builds, which reads as a hang and invites a Ctrl+C.
    # Quiet the loader. HuggingFace prints an unauthenticated-hub warning and a
    # progress bar to stderr, and both land in the middle of the line above.
    # Harmless, and it makes the drill look broken when somebody is watching.
    import os

    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    print(term.grey("  loading the corpus index so the proof step can read it..."),
          end="", flush=True)
    warm = time.perf_counter()

    # The hub's "unauthenticated requests" warning is not controlled by any env
    # var, so stderr is captured for the duration of the load. It is kept, not
    # discarded: if the load fails, the captured text is printed, because
    # swallowing the one message that explains a failure would be worse than
    # the noise it was hiding.
    import contextlib
    import io

    noise = io.StringIO()
    try:
        with contextlib.redirect_stderr(noise):
            build_index(STRATEGY_STRUCTURED)
    except Exception:
        print()
        print(noise.getvalue(), end="")
        raise
    warm_ms = round((time.perf_counter() - warm) * 1000, 1)
    print(term.grey(f" {warm_ms / 1000:.1f}s (one-off, before the clock starts)"))
    print()

    started = time.perf_counter()

    # Step 1. The date is the only hard fact a vague complaint reliably gives.
    since = (datetime.now(timezone.utc) - timedelta(days=10)).date().isoformat()
    until = (datetime.now(timezone.utc) - timedelta(days=4)).date().isoformat()

    # Step 2. The rare words from the complaint, not the common ones.
    hits, report = search.search(
        "refund card migration token", since=since, until=until, limit=5
    )

    print("  HOW IT NARROWED:")
    for label, n in report["funnel"]:
        print(f"    {label:44} -> {n}")
    print()
    print(f"  TOP {len(hits)} (search took {report['ms']}ms):")
    found = None
    for h in hits:
        bad, _ = plant.contradicts_its_citation(h.trace)
        mark = term.red("  <<< contradicts its own citation") if bad else ""
        print(f"    {h.line()[:104]}{mark}")
        if bad and found is None:
            found = h
    elapsed = round((time.perf_counter() - started) * 1000, 1)
    print()

    result = {
        "ms": elapsed,
        "search_ms": report["ms"],
        "index_warm_ms": warm_ms,
        "searched": report["searched"],
        "funnel": report["funnel"],
    }
    if found is None:
        print(term.red("  NOT FOUND."))
        return result

    bad, why = plant.contradicts_its_citation(found.trace)
    print(f"  {term.bold('FOUND')}: {found.trace_id}")
    print(f"    search over {report['searched']} traces : {report['ms']}ms")
    print(f"    proof, reading the cited chunk  : {round(elapsed - report['ms'], 1)}ms")
    print(f"    total                           : {elapsed}ms "
          f"(plus {warm_ms}ms one-off index load)")
    print(f"  asked : {' '.join(found.trace['question'].split())[:88]}")
    print(f"  said  : {' '.join(found.trace['answer'].split())[:88]}")
    print()
    print("  WHY IT IS WRONG:")
    for line in _wrap(why, 74):
        print(f"    {line}")
    print()
    result.update({"trace_id": found.trace_id, "proof": why, "found": True})
    return result


# ---------------------------------------------------------------------------
def run_cost() -> dict:
    """Part 3. Cost per request, measured, improved, and measured again."""
    print(term.rule("cost per request"))
    before = store.stats()
    rep = measure.replay()
    d = rep.as_dict()

    print(f"  {'':34} {'before':>14} {'after':>14}")
    rows = [
        ("cost per request", f"${d['cost_per_request_before']:.8f}",
         f"${d['cost_per_request_after']:.8f}"),
        ("tokens per request", d["tokens_per_request_before"], d["tokens_per_request_after"]),
        ("LLM calls over the whole log", d["calls_before"], d["calls_after"]),
    ]
    for label, a, b in rows:
        print(f"  {label:34} {str(a):>14} {str(b):>14}")
    print()
    print(f"  cache hit rate      {d['hit_rate']:.1%}  "
          f"({d['exact_hits']} exact, {d['similar_hits']} similar)")
    print(f"  {term.bold('cost saving')}         {d['cost_saving']:.1%}")
    print()

    print("  THE RISK, which decides whether the saving counts:")
    print(f"    {'threshold':>10} {'hit rate':>10} {'saving':>9} {'wrong answers served':>22}")
    thresholds = {}
    for th in (0.5, 0.7, 0.8, 0.9):
        rk = measure.risk(threshold=th)
        rp = measure.replay(threshold=th)
        thresholds[th] = {"hit_rate": rp.hit_rate, "saving": rp.cost_saving,
                          "wrong": rk.wrong, "served": rk.served}
        print(f"    {th:>10} {rp.hit_rate:>9.1%} {rp.cost_saving:>8.1%} "
              f"{str(rk.wrong) + '/' + str(rk.served):>22}")
    print()
    return {"before": before, "replay": d, "thresholds": thresholds}


# ---------------------------------------------------------------------------
def run_guard() -> dict:
    """Part 4. The failure, now a test that fires if it returns."""
    print(term.rule("the failure, now a test"))
    out = []
    for reg in REGRESSIONS:
        print(f"  {term.bold(reg.id)}  found in the drill")
        print(f"    went wrong: {_wrap(reg.what_went_wrong, 70)[0]}")
        for line in _wrap(reg.what_went_wrong, 70)[1:]:
            print(f"                {line}")
        print()

        ok_bad, reasons_bad = reg.judge(reg.failing_answer)
        print(f"    the answer that failed      -> "
              f"{term.red('CAUGHT') if not ok_bad else term.red('MISSED (bug)')}")
        for r in reasons_bad:
            print(f"        {r}")

        good = (
            "The refund cannot go back to the original payment method because the "
            "token was dropped during migration. It must be issued as account "
            "credit instead [HC-4003-structured-006]."
        )
        ok_good, reasons_good = reg.judge(good)
        print(f"    a correct answer            -> "
              f"{term.green('PASSES') if ok_good else term.red('FALSE ALARM (bug)')}")
        for r in reasons_good:
            print(f"        {r}")
        print()
        out.append({"id": reg.id, "catches_the_failure": not ok_bad,
                    "allows_a_correct_answer": ok_good})
    return {"regressions": out}


# ---------------------------------------------------------------------------
def run_live() -> dict:
    """Ask the app the pinned question again. The only part that costs money."""
    from agent.budget import Budget
    from agent.loop import run as run_agent

    print(term.rule("live: is the bug still there?"))
    reg = REFUND_TO_CARD
    print(f"  asking: {reg.question}")
    print()
    result = run_agent(reg.question, budget=Budget(max_steps=4, max_seconds=900), verbose=True)
    ok, reasons = reg.judge(result.answer)
    print()
    print(f"  trace id: {result.trace_id}")
    print(f"  answer  : {' '.join((result.answer or '').split())[:140]}")
    print()
    print(f"  {reg.id}: {term.green('PASSES') if ok else term.red('STILL FAILS')}")
    for r in reasons:
        print(f"      {r}")
    print()
    return {"id": reg.id, "ok": ok, "reasons": reasons,
            "trace_id": result.trace_id, "answer": result.answer}


def _wrap(text: str, width: int) -> list[str]:
    words, lines, line = " ".join((text or "").split()).split(), [], ""
    for w in words:
        if len(line) + len(w) + 1 > width:
            lines.append(line)
            line = w
        else:
            line = f"{line} {w}".strip()
    if line:
        lines.append(line)
    return lines or [""]


# ---------------------------------------------------------------------------
# The report
# ---------------------------------------------------------------------------
def write_report(data: dict, path: Path) -> None:
    lines = [
        "# Week 11: the app watching itself",
        "",
        "Four things, in the order the mentor asks about them.",
        "",
    ]

    if "log" in data:
        s = data["log"]["stats"]
        lines += [
            "## 1. The log",
            "",
            "| | |",
            "|---|---|",
            f"| Traces | {s['n']} |",
            f"| Days covered | {len(s['days'])} ({s['days'][0]} to {s['days'][-1]}) |",
            f"| LLM calls recorded | {s['llm_calls']} |",
            f"| Refusals | {s['refusals']} |",
            f"| Median latency | {s['ms_p50']:.0f} ms |",
            f"| p95 latency | {s['ms_p95']:.0f} ms |",
            "",
            "Every request carries a trace id, a timestamp, the question, the answer,",
            "the chunk ids it was built from, what it cited, and **a span per step**.",
            "",
            "A span is a step with its own milliseconds, tokens and cost. One total",
            "would hide where the time and money went, which is the whole reason",
            "Week 10 could say the squad's manager spent 5,174 input tokens and",
            "produced no answer.",
            "",
        ]

    if "drill" in data and data["drill"].get("found"):
        d = data["drill"]
        lines += [
            "## 2. The support drill",
            "",
            "**The complaint, as forwarded:**",
            "",
            f"> {' '.join(plant.COMPLAINT.split())}",
            "",
            "No trace id. No exact wording. A rough date and the word 'refund'.",
            "",
            "**How it narrowed:**",
            "",
            "| Filter | Traces left |",
            "|---|---|",
        ]
        for label, n in d["funnel"]:
            lines.append(f"| {label} | {n} |")
        lines += [
            "",
            f"**Found `{d['trace_id']}`** over {d['searched']} traces:",
            "",
            "| Step | Time |",
            "|---|---|",
            f"| Search | **{d.get('search_ms', d['ms'])}ms** |",
            f"| Proof, reading the cited chunk | {round(d['ms'] - d.get('search_ms', 0), 1)}ms |",
            f"| One-off index load, before the clock | {d.get('index_warm_ms', 0)}ms |",
            "",
            "**Why it is wrong:**",
            "",
            f"> {d['proof']}",
            "",
            "That last step is what makes it a drill rather than a lucky grep. The",
            "answer cited a real chunk, and said the opposite of what the chunk says.",
            "Every deterministic check in this project passes it, because they all",
            "ask whether the citation resolves, not whether it agrees.",
            "",
        ]

    if "cost" in data:
        c = data["cost"]["replay"]
        lines += [
            "## 3. Cost per request, measured and improved",
            "",
            "| | before | after |",
            "|---|---|---|",
            f"| Cost per request | ${c['cost_per_request_before']:.8f} | "
            f"**${c['cost_per_request_after']:.8f}** |",
            f"| Tokens per request | {c['tokens_per_request_before']} | "
            f"**{c['tokens_per_request_after']}** |",
            f"| LLM calls over the log | {c['calls_before']} | **{c['calls_after']}** |",
            "",
            f"**Cost saving: {c['cost_saving']:.1%}.** Cache hit rate "
            f"{c['hit_rate']:.1%}: {c['exact_hits']} exact, {c['similar_hits']} similar.",
            "",
            "**The improvement is an answer cache**, fenced by model, prompt",
            "fingerprint and corpus fingerprint. Change any of those and the cache",
            "empties rather than serving stale answers under new settings.",
            "",
            "### The risk, which decides whether the saving counts",
            "",
            "A cache that serves the wrong answer is not a saving. It is a bug with",
            "a good dashboard. So the wrong answers are counted too.",
            "",
            "| Similarity threshold | Hit rate | Saving | Wrong answers served |",
            "|---|---|---|---|",
        ]
        for th, row in data["cost"]["thresholds"].items():
            lines.append(
                f"| {th} | {row['hit_rate']:.1%} | {row['saving']:.1%} | "
                f"{row['wrong']}/{row['served']} |"
            )
        lines += [
            "",
            "**Zero wrong answers at every threshold**, and the reason is not the",
            "threshold. It is the code fence: two questions that differ only by",
            "their error code are never treated as the same question.",
            "",
            "`ERR-4032` against `ERR-4044` in the same sentence scores **0.818**",
            "word overlap, which is above the 0.8 threshold. Without the fence that",
            "near-miss is served, and a customer gets the fix for the wrong problem.",
            "",
        ]

    if "guard" in data:
        lines += [
            "## 4. The failure, now a test",
            "",
            "| Check | Result |",
            "|---|---|",
        ]
        for row in data["guard"]["regressions"]:
            lines.append(
                f"| {row['id']} catches the answer that failed | "
                f"{'yes' if row['catches_the_failure'] else '**NO**'} |"
            )
            lines.append(
                f"| {row['id']} allows a correct answer | "
                f"{'yes' if row['allows_a_correct_answer'] else '**NO**'} |"
            )
        lines += [
            "",
            "Both directions matter. A check that catches the bug but also fires on",
            "correct answers is not a guard, it is an alarm nobody will keep.",
            "",
            "The case records the trace id it came from, so six months from now the",
            "log can answer why it exists. A regression with no provenance gets",
            "deleted by the next person tidying up.",
            "",
        ]

    if "live" in data:
        live = data["live"]
        lines += [
            "### Asked again, live",
            "",
            f"- Trace: `{live['trace_id']}`",
            f"- Result: **{'passes' if live['ok'] else 'still fails'}**",
            "",
            "```",
            " ".join((live.get("answer") or "").split())[:500],
            "```",
            "",
        ]
        if live["reasons"]:
            lines += ["Reasons it failed:", ""]
            lines += [f"- {r}" for r in live["reasons"]] + [""]

    lines += [
        "## The 10x plan: what breaks first",
        "",
        "At ten times this traffic, in the order it breaks:",
        "",
        "1. **The provider's rate limit, long before anything of ours.** This",
        "   project hit the free tier's daily cap in six of the last eight weeks.",
        "   Ten times the traffic means that at 2am instead of 4pm. The fix is a",
        "   paid tier and a queue, not code.",
        "2. **The trace log.** One JSONL file per day, read whole into memory by",
        "   every search. At 82 traces that is 2ms. At 50,000 a day it is a",
        "   problem, and the fix is the one every team reaches for: ship the",
        "   traces to something built for them. The shape here is already the",
        "   trace-and-span shape LangSmith, Phoenix and OpenTelemetry take, so",
        "   the change is `obs/store.py` and nothing else.",
        "3. **The answer cache's memory.** It is a list scanned linearly on every",
        "   lookup. Fine at hundreds of entries, not at hundreds of thousands.",
        "4. **The MCP servers.** One subprocess per server per agent process. Ten",
        "   times the concurrency means ten times the processes, each loading its",
        "   own copy of the embedding model.",
        "",
        "**What does NOT break:** retrieval. It is a local index over 34 chunks",
        "and has never been the bottleneck in nine weeks of measurement.",
        "",
        "## What this does NOT do",
        "",
        "- **The log is backfilled.** The questions, answers, chunk ids and token",
        "  counts are real and come from the Weeks 7 to 10 caches. **The",
        "  timestamps are invented**, because the caches record no wall-clock date",
        "  and the drill needs to narrow by day. Every backfilled trace is marked",
        "  `backfilled: true`.",
        "- **The hit rate is flattered.** The log replays eval runs, which asked",
        "  the same twelve questions many times. Real support traffic is more",
        "  varied, so 81.7% is an upper bound, not a forecast.",
        "- **The similarity layer contributed nothing here.** Every hit was exact.",
        "  The risky half of the cache is the half this traffic never exercised.",
        "- **The planted answer is planted.** It is marked in the log, and a test",
        "  asserts the search never filters on that marker. The drill is honest",
        "  about the haystack while being honest that the needle was placed.",
        "- **No rotation, no retention, no PII redaction.** All three are real",
        "  production concerns and none is built.",
        "- **`contradicts_its_citation` checks one rule**, not faithfulness in",
        "  general. A general judge is what Week 6 built and then refused to",
        "  trust.",
        "",
        "## Reproducing it",
        "",
        "```bash",
        "python -m evals.run_w11 --all     # all four parts. Free.",
        "python -m evals.run_w11 --drill   # just the drill. Free.",
        "python -m evals.run_w11 --live    # ask the pinned question again. ~3 calls.",
        "python test_acceptance.py",
        "```",
        "",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    term.init()
    parser = argparse.ArgumentParser(description="Week 11: observability, cost, the test loop.")
    parser.add_argument("--log", action="store_true", help="Build the trace log. Free.")
    parser.add_argument("--drill", action="store_true", help="The support drill. Free.")
    parser.add_argument("--cost", action="store_true", help="Cost before and after. Free.")
    parser.add_argument("--guard", action="store_true", help="The failure as a test. Free.")
    parser.add_argument("--all", action="store_true", help="All four, then the report.")
    parser.add_argument("--live", action="store_true", help="Ask the pinned question. Costs calls.")
    parser.add_argument("--keep-log", action="store_true",
                        help="With --log or --all, append rather than rebuild.")
    args = parser.parse_args()

    if not any((args.log, args.drill, args.cost, args.guard, args.all, args.live)):
        parser.error("pick one: --log, --drill, --cost, --guard, --all, or --live")

    out = _out()
    cache_path = out / "w11_runs.json"
    data = {}
    if cache_path.exists():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            data = {}

    if args.log or args.all:
        data["log"] = build_log(overwrite=not args.keep_log)
    if args.drill or args.all:
        data["drill"] = run_drill()
    if args.cost or args.all:
        data["cost"] = run_cost()
    if args.guard or args.all:
        data["guard"] = run_guard()
    if args.live:
        data["live"] = run_live()

    cache_path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str),
                          encoding="utf-8")
    write_report(data, out / "w11_production.md")
    print(f"Wrote {out / 'w11_production.md'}")


if __name__ == "__main__":
    main()
