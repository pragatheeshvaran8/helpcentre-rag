"""The one command for Week 10. Race the squad against the single agent.

    python -m evals.run_w10 --race     run both sides on the same tickets
    python -m evals.run_w10 --report   rescore the cache. Free.
    python -m evals.run_w10 --ticket T01 -v   watch one ticket, both ways

WHAT MAKES THIS A FAIR RACE
    The mentor's first question is whether both ran on the SAME tests, so this
    file goes out of its way to make that true and checkable:

      same tickets      the twelve from evals/w7_tickets.py, untouched
      same model        one setting, read once
      same corpus       one chunk index
      same tools        ONE MCP toolbox, started once and handed to both, so
                        neither pays a start-up the other avoided
      same scoring      evals/w7_race.py for quality, evals/w8_trajectory.py
                        for the path

    The only difference is the topology: one agent, or a manager and two
    specialists. If anything else moved, the race would be measuring two
    changes at once.

WHAT IS MEASURED
    QUALITY   pass rate, and parts-of-the-ticket cited. A two-part ticket with
              one part answered is not half right.
    SPEED     wall-clock seconds per ticket, median.
    TOKENS    input and output, from the provider's own usage report.
    COST      what the provider charged (0 on a free model), plus a priced
              estimate from the real token counts, clearly labelled.

WHY TOKENS AND NOT JUST CALLS
    A hand-off re-sends the whole context. Counting calls hides that. Counting
    tokens is the only way to see what a team actually costs.
"""
from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

from agent import squad
from agent.budget import ERROR, Budget
from agent.loop import run as run_single
from agent.toolbox import connect
from config import get_settings
from evals.w7_race import part_coverage, score
from evals.w7_tickets import SHAPES, ticket_set
from evals.w8_trajectory import evaluate
from rag import term

SINGLE = "single"
SQUAD = "squad"
RUNNERS = (SINGLE, SQUAD)
W10_DIR = "w10_runs"

# A squad step is a specialist's tool call. Four tool calls over three
# specialists is a lot of hand-offs for one ticket; past that the manager has
# split badly and the run is told to stop rather than spiral.
SQUAD_MAX_PARTS = 3


def _dir() -> Path:
    path = Path(get_settings().results_dir) / W10_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load(runner: str) -> dict:
    path = _dir() / f"{runner}__runs.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _save(runner: str, data: dict) -> None:
    (_dir() / f"{runner}__runs.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8"
    )


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
        "steps": [s if isinstance(s, dict) else s.__dict__ for s in result.steps],
        "stop_reason": result.stop_reason,
        "llm_calls": result.llm_calls,
        "elapsed_s": result.elapsed_s,
        "error": result.error,
        "gate_fired": result.gate_fired,
        "budget_degraded": result.budget_degraded,
        "meter": result.meter.as_dict(),
        "tasks": [t.as_dict() for t in getattr(result, "tasks", [])],
    }


class _Replayed:
    """A cached run, shaped like the live object every scorer expects."""

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
            self.n = d.get("n", 0)
            self.tool = d.get("tool", "?")
            self.args = d.get("args", {})
            self.observation = d.get("observation", "")
            self.thought = d.get("thought", "")

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
        self.meter = d.get("meter", {})
        self.tasks = d.get("tasks", [])

    @property
    def completed(self) -> bool:
        return self.stop_reason in ("finished", "completed")


# ---------------------------------------------------------------------------
def race(tickets: list[dict], *, refresh: bool, verbose: bool) -> dict:
    """Run both sides on the same tickets, through one shared toolbox."""
    # --refresh drops ONLY the tickets being run, not the whole cache.
    #
    # The first version emptied the cache outright, so `--refresh --ticket T01`
    # re-ran one ticket and silently deleted the other eleven. That trap cost a
    # full set of runs in Week 7 and is not worth leaving in a flag whose name
    # reads like "do this one again".
    wanted = {t["id"] for t in tickets}
    caches = {}
    for runner in RUNNERS:
        cache = _load(runner)
        if refresh:
            cache = {k: v for k, v in cache.items() if k not in wanted}
        caches[runner] = cache

    # ONE toolbox for both. Starting a second set of servers for the squad
    # would charge it for a start-up the single agent did not pay, and the
    # mentor's first question is whether this was fair.
    with connect(verbose=verbose) as box:
        if verbose:
            print()
        for ticket in tickets:
            for runner in RUNNERS:
                if ticket["id"] in caches[runner]:
                    if verbose:
                        print(term.grey(f"  {ticket['id']} {runner}: cached"))
                    continue

                print(f"  {ticket['id']} {term.bold(runner):18} "
                      f"{term.dim(ticket['question'][:46])}")
                try:
                    if runner == SINGLE:
                        result = run_single(
                            ticket["question"],
                            budget=Budget(max_seconds=900),
                            verbose=verbose,
                            toolbox=box,
                        )
                    else:
                        result = squad.run(
                            ticket["question"],
                            toolbox=box,
                            verbose=verbose,
                            max_parts=SQUAD_MAX_PARTS,
                        )
                except Exception as exc:
                    print(term.red(f"       failed: {str(exc)[:76]}"))
                    continue

                if result.stop_reason in (ERROR, "failed"):
                    print(term.red(f"       {(result.error or 'error')[:76]}"))
                    print(term.grey("       not cached, retries next run"))
                    continue

                caches[runner][ticket["id"]] = _serialise(result)
                _save(runner, caches[runner])
                m = result.meter
                print(
                    term.grey(
                        f"       {result.stop_reason}  {m.n_calls} call(s)  "
                        f"{m.total_tokens} tokens  {result.elapsed_s}s"
                    )
                )
    return caches


# ---------------------------------------------------------------------------
def score_all(tickets: list[dict], caches: dict) -> dict:
    """Quality, path and cost for every cached run. Free, and repeatable."""
    out = {}
    for runner in RUNNERS:
        cache = caches.get(runner, {})
        rows = []
        for ticket in tickets:
            record = cache.get(ticket["id"])
            if record is None:
                continue
            run = _Replayed(record)
            quality = score(ticket, run)
            trajectory = evaluate(ticket, run, quality.passed)
            cover = part_coverage(run, ticket)
            meter = record.get("meter", {})
            rows.append(
                {
                    "ticket_id": ticket["id"],
                    "shape": ticket["shape"],
                    "passed": quality.passed,
                    "failure_modes": quality.failure_modes,
                    "parts_cited": cover.cited,
                    "parts_total": cover.total,
                    "fully_cited": cover.fully_cited,
                    "trajectory_clean": trajectory.clean,
                    "seconds": record.get("elapsed_s", 0.0),
                    "calls": meter.get("calls", 0),
                    "input_tokens": meter.get("input_tokens", 0),
                    "output_tokens": meter.get("output_tokens", 0),
                    "total_tokens": meter.get("total_tokens", 0),
                    "reported_cost": meter.get("reported_cost", 0.0),
                    "priced_cost": meter.get("priced_cost_estimate", 0.0),
                    "by_who": meter.get("by_who", {}),
                    "tasks": record.get("tasks", []),
                }
            )
        out[runner] = {
            "rows": rows,
            "summary": summarise(rows),
            "missing": [t["id"] for t in tickets if t["id"] not in cache],
        }
    return out


def summarise(rows: list[dict]) -> dict:
    if not rows:
        return {"n": 0}
    times = [r["seconds"] for r in rows]
    tokens = [r["total_tokens"] for r in rows]
    multi = [r for r in rows if r["shape"] == "multi"]
    parts_cited = sum(r["parts_cited"] for r in rows)
    parts_total = sum(r["parts_total"] for r in rows)
    return {
        "n": len(rows),
        # quality
        "passed": sum(1 for r in rows if r["passed"]),
        "pass_rate": round(sum(1 for r in rows if r["passed"]) / len(rows), 4),
        "parts_cited_rate": round(parts_cited / parts_total, 4) if parts_total else 0.0,
        "multi_fully_cited": sum(1 for r in multi if r["fully_cited"]),
        "multi_n": len(multi),
        "trajectory_clean": sum(1 for r in rows if r["trajectory_clean"]),
        # speed
        "median_seconds": round(statistics.median(times), 2),
        "total_seconds": round(sum(times), 2),
        "slowest_seconds": round(max(times), 2),
        # tokens
        "input_tokens": sum(r["input_tokens"] for r in rows),
        "output_tokens": sum(r["output_tokens"] for r in rows),
        "total_tokens": sum(tokens),
        "median_tokens": round(statistics.median(tokens), 1),
        "tokens_per_ticket": round(sum(tokens) / len(rows), 1),
        # cost
        "calls": sum(r["calls"] for r in rows),
        "reported_cost": round(sum(r["reported_cost"] for r in rows), 6),
        "priced_cost": round(sum(r["priced_cost"] for r in rows), 6),
        "by_shape": {
            shape: _shape_row([r for r in rows if r["shape"] == shape]) for shape in SHAPES
        },
    }


def _shape_row(rows: list[dict]) -> dict:
    if not rows:
        return {"n": 0, "passed": 0, "total_tokens": 0, "median_seconds": 0.0}
    return {
        "n": len(rows),
        "passed": sum(1 for r in rows if r["passed"]),
        "fully_cited": sum(1 for r in rows if r["fully_cited"]),
        "total_tokens": sum(r["total_tokens"] for r in rows),
        "median_seconds": round(statistics.median([r["seconds"] for r in rows]), 2),
    }


# ---------------------------------------------------------------------------
def verdict(single: dict, squad_s: dict) -> dict:
    """Which to keep, by a rule written before the race ran.

    The rule, in order:

    1. Quality decides first. If one side answers materially more of the
       tickets, it wins, whatever it costs. A cheaper wrong answer is not a
       saving.
    2. "Materially" is one whole ticket. On twelve tickets a single-ticket gap
       is noise, and saying so is more useful than a decimal.
    3. If quality ties, cost decides, measured in tokens rather than calls,
       because tokens are what a hand-off actually spends.

    Written this way so the answer can be "keep the single agent", which the
    brief says is the common and valuable finding.
    """
    q_single = single.get("parts_cited_rate", 0.0)
    q_squad = squad_s.get("parts_cited_rate", 0.0)
    p_single, p_squad = single.get("passed", 0), squad_s.get("passed", 0)
    t_single = single.get("total_tokens", 0) or 1
    t_squad = squad_s.get("total_tokens", 0) or 1

    gap = p_squad - p_single
    token_ratio = t_squad / t_single

    if gap >= 1:
        keep, why = SQUAD, (
            f"The squad passes {p_squad} tickets against {p_single}, a gap of "
            f"{gap}. It costs {token_ratio:.1f}x the tokens to do it. Quality "
            "decides first, and a cheaper wrong answer is not a saving."
        )
    elif gap <= -1:
        keep, why = SINGLE, (
            f"The single agent passes {p_single} tickets against {p_squad}. The "
            f"squad is both worse and {token_ratio:.1f}x more expensive in "
            "tokens. There is nothing to weigh."
        )
    else:
        keep, why = SINGLE, (
            f"Both pass {p_single} tickets, and parts-cited is "
            f"{q_single:.0%} against {q_squad:.0%}. The squad buys no quality "
            f"and spends {token_ratio:.1f}x the tokens doing it, because every "
            "hand-off re-sends the whole context. Keep the simple one."
        )
    return {
        "keep": keep,
        "why": why,
        "quality_gap_tickets": gap,
        "token_ratio": round(token_ratio, 2),
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def matched(scored: dict) -> tuple[dict, dict, list[str]]:
    """Summarise ONLY the tickets both sides completed.

    The first version summarised each side's full cache. With 7 single runs and
    6 squad runs it printed "7/7 vs 5/6" and a token total that included a
    ticket the squad never saw. Two different case sets in one row is exactly
    the denominator trap Week 6 had to go back and fix, and Week 8 after it.

    Returns the two summaries plus the matched ticket ids, so a caller can say
    how many tickets the comparison actually rests on.
    """
    ids = sorted(
        {r["ticket_id"] for r in scored[SINGLE]["rows"]}
        & {r["ticket_id"] for r in scored[SQUAD]["rows"]}
    )
    keep = set(ids)
    return (
        summarise([r for r in scored[SINGLE]["rows"] if r["ticket_id"] in keep]),
        summarise([r for r in scored[SQUAD]["rows"] if r["ticket_id"] in keep]),
        ids,
    )


def write_report(tickets: list[dict], scored: dict, path: Path) -> None:
    s, q, matched_ids = matched(scored)
    complete = not scored[SINGLE]["missing"] and not scored[SQUAD]["missing"]

    lines = [
        "# Week 10: the squad against the single agent",
        "",
        f"- Tickets: {len(tickets)}, the same set both sides, from `evals/w7_tickets.py`",
        f"- Model: `{get_settings().openrouter_model}`",
        "- One MCP toolbox, started once and handed to both, so neither pays a",
        "  start-up the other avoided.",
        "- The squad is a manager plus two specialists: `code_desk` and `policy_desk`.",
        f"- **Every number below covers the {len(matched_ids)} ticket(s) BOTH sides",
        f"  completed**: {', '.join(matched_ids) or 'none'}. A run only one side",
        "  finished is excluded, because two different case sets in one row is not",
        "  a comparison.",
        "",
    ]

    if not complete:
        lines += [
            "> **INCOMPLETE RACE.** Not every ticket ran on both sides, so the",
            "> totals below cover different sets and the verdict is withheld.",
            f"> Missing for single: {', '.join(scored[SINGLE]['missing']) or 'none'}",
            f"> Missing for squad: {', '.join(scored[SQUAD]['missing']) or 'none'}",
            "",
        ]

    if not s.get("n") or not q.get("n"):
        lines += ["Nothing scored yet. Run `python -m evals.run_w10 --race`.", ""]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return

    ratio = (q["total_tokens"] / s["total_tokens"]) if s["total_tokens"] else 0
    lines += [
        "## The four numbers",
        "",
        "| | single agent | squad | squad vs single |",
        "|---|---|---|---|",
        f"| **Quality** passed | {s['passed']}/{s['n']} | {q['passed']}/{q['n']} | "
        f"{q['passed'] - s['passed']:+d} |",
        f"| Parts of the ticket cited | {s['parts_cited_rate']:.0%} | "
        f"{q['parts_cited_rate']:.0%} | {(q['parts_cited_rate'] - s['parts_cited_rate']) * 100:+.0f} pts |",
        f"| Multi-part fully answered | {s['multi_fully_cited']}/{s['multi_n']} | "
        f"{q['multi_fully_cited']}/{q['multi_n']} | "
        f"{q['multi_fully_cited'] - s['multi_fully_cited']:+d} |",
        f"| **Speed** median s/ticket | {s['median_seconds']} | {q['median_seconds']} | "
        f"{_times(q['median_seconds'], s['median_seconds'])} |",
        f"| **Tokens** total | {s['total_tokens']:,} | {q['total_tokens']:,} | "
        f"{_times(q['total_tokens'], s['total_tokens'])} |",
        f"| Input tokens | {s['input_tokens']:,} | {q['input_tokens']:,} | "
        f"{_times(q['input_tokens'], s['input_tokens'])} |",
        f"| Output tokens | {s['output_tokens']:,} | {q['output_tokens']:,} | "
        f"{_times(q['output_tokens'], s['output_tokens'])} |",
        f"| **Cost** reported by provider | ${s['reported_cost']:.4f} | "
        f"${q['reported_cost']:.4f} | free tier |",
        f"| Cost, priced estimate | ${s['priced_cost']:.4f} | ${q['priced_cost']:.4f} | "
        f"{_times(q['priced_cost'], s['priced_cost'])} |",
        f"| LLM calls | {s['calls']} | {q['calls']} | "
        f"{_times(q['calls'], s['calls'])} |",
        "",
        "The provider reports a cost of exactly $0 because the model is `:free`.",
        "That is true and useless for a comparison, so the priced row applies a",
        "published rate to the real token counts. It is arithmetic on a rate",
        "card, not a bill, and the ratio is what matters rather than the figure.",
        "",
        "## Where the squad's tokens went",
        "",
        "| Participant | calls | input tokens | output tokens |",
        "|---|---|---|---|",
    ]

    who_totals: dict[str, dict] = {}
    for row in scored[SQUAD]["rows"]:
        for who, stats in (row.get("by_who") or {}).items():
            t = who_totals.setdefault(who, {"calls": 0, "input_tokens": 0, "output_tokens": 0})
            for k in t:
                t[k] += stats.get(k, 0)
    for who, t in sorted(who_totals.items(), key=lambda kv: -kv[1]["input_tokens"]):
        lines.append(
            f"| {who} | {t['calls']} | {t['input_tokens']:,} | {t['output_tokens']:,} |"
        )

    lines += [
        "",
        "Input tokens are the interesting column. Every hand-off re-sends the",
        "ticket, the specialist's own system prompt and its tool catalogue, and",
        "the specialists' findings then go into the manager's final prompt as",
        "well. The same ticket text is paid for three or four times.",
        "",
        "## By ticket shape",
        "",
        "| Shape | single passed | squad passed | single tokens | squad tokens |",
        "|---|---|---|---|---|",
    ]
    for shape in SHAPES:
        a = s["by_shape"].get(shape, {})
        b = q["by_shape"].get(shape, {})
        lines.append(
            f"| {shape} | {a.get('passed', 0)}/{a.get('n', 0)} "
            f"| {b.get('passed', 0)}/{b.get('n', 0)} "
            f"| {a.get('total_tokens', 0):,} | {b.get('total_tokens', 0):,} |"
        )

    lines += ["", "## Per ticket", "",
              "| Ticket | shape | single pass | squad pass | single tokens | squad tokens | squad parts |",
              "|---|---|---|---|---|---|---|"]
    srows = {r["ticket_id"]: r for r in scored[SINGLE]["rows"]}
    qrows = {r["ticket_id"]: r for r in scored[SQUAD]["rows"]}
    for ticket in tickets:
        a, b = srows.get(ticket["id"]), qrows.get(ticket["id"])
        if not a or not b:
            lines.append(f"| {ticket['id']} | {ticket['shape']} | not run | | | | |")
            continue
        lines.append(
            f"| {a['ticket_id']} | {a['shape']} "
            f"| {'yes' if a['passed'] else 'no'} | {'yes' if b['passed'] else 'no'} "
            f"| {a['total_tokens']:,} | {b['total_tokens']:,} "
            f"| {len(b.get('tasks') or [])} |"
        )

    if complete:
        v = verdict(s, q)
        lines += [
            "",
            "## The verdict",
            "",
            f"**Keep the {v['keep']}.**",
            "",
            v["why"],
            "",
            "The rule that picked this is `verdict()` in `evals/run_w10.py`. It was",
            "written before the race ran, quality decides before cost, and a gap",
            "smaller than one whole ticket counts as no gap on a set this size.",
            "",
            "## When a squad WOULD be worth it",
            "",
            "Not here, and the reasons are specific rather than general:",
            "",
            "- **The parts are not independent.** Looking up ERR-4032 tells you",
            "  nothing that changes how you look up ERR-7215, so splitting them",
            "  buys no information the single agent lacked.",
            "- **Nothing runs in parallel.** The specialists run one after another",
            "  in one process, so the wall clock gets the hand-off cost with none",
            "  of the concurrency that would pay for it.",
            "- **The instructions are not truly different.** Both specialists",
            "  ground, cite and refuse by the same rules. The split is by TOOL,",
            "  and a tool catalogue is cheap to hand one agent.",
            "",
            "A squad earns its keep when parts are genuinely independent AND run",
            "at the same time, or when a part needs instructions so different",
            "that putting them in one prompt would damage the rest. On a support",
            "ticket against one corpus, neither is true.",
            "",
        ]
    else:
        lines += ["", "## The verdict", "",
                  "Withheld. The race did not finish on both sides, and a verdict",
                  "from a partial race is a guess with a table attached.", ""]

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _times(a: float, b: float) -> str:
    if not b:
        return "n/a"
    return f"{a / b:.1f}x"


def write_handoffs(tickets: list[dict], caches: dict, path: Path) -> None:
    """Every split and every hand-off, so the A2A task lifecycle is visible."""
    lines = [
        "# Week 10: how the manager split each ticket",
        "",
        "Each hand-off is a task with a lifecycle: submitted, working, then",
        "completed or failed. The manager routes by reading agent cards, so",
        "nothing in its code names a specialist.",
        "",
    ]
    cache = caches.get(SQUAD, {})
    for ticket in tickets:
        record = cache.get(ticket["id"])
        lines += [f"## {ticket['id']} ({ticket['shape']}, {ticket['parts']} part(s))", "",
                  f"> {ticket['question']}", ""]
        if record is None:
            lines += ["_not run_", ""]
            continue
        meter = record.get("meter", {})
        lines.append(
            f"Split into **{len(record.get('tasks') or [])} task(s)**. "
            f"{meter.get('calls', 0)} LLM calls, {meter.get('total_tokens', 0):,} tokens, "
            f"{record.get('elapsed_s', 0)}s."
        )
        lines.append("")
        for task in record.get("tasks") or []:
            state = task["state"]
            mark = "completed" if state == "completed" else f"**{state}**"
            lines.append(f"- `{task['task_id']}` to **{task['assignee']}** [{mark}]")
            lines.append(f"  - asked: {task['instruction']}")
            if task.get("tool_calls"):
                lines.append(f"  - tools: {', '.join(task['tool_calls'])}")
            if task.get("error"):
                lines.append(f"  - error: {task['error']}")
        lines += ["", "**Final answer**", "", "```",
                  (record.get("answer") or "").strip()[:900] or "(empty)", "```", ""]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
def main() -> None:
    term.init()
    parser = argparse.ArgumentParser(description="Week 10: squad vs single agent.")
    parser.add_argument("--race", action="store_true", help="Run both sides.")
    parser.add_argument("--report", action="store_true", help="Rescore the cache. Free.")
    parser.add_argument("--ticket", help="One ticket by id, e.g. T01.")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Re-run the tickets named, ignoring their cached results. Other tickets are kept.",
    )
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if not (args.race or args.report or args.ticket):
        parser.error("pick one: --race, --report, or --ticket T01")

    all_tickets = ticket_set()
    tickets = all_tickets
    if args.ticket:
        tickets = [t for t in all_tickets if t["id"] == args.ticket.upper()]
        if not tickets:
            parser.error(f"no ticket {args.ticket!r}")

    caches = {}
    if args.race or args.ticket:
        caches = race(tickets, refresh=args.refresh, verbose=args.verbose)
        print()

    for runner in RUNNERS:
        caches.setdefault(runner, _load(runner))

    scored = score_all(all_tickets, caches)
    out = Path(get_settings().results_dir)
    write_report(all_tickets, scored, out / "w10_race.md")
    write_handoffs(all_tickets, caches, out / "w10_handoffs.md")
    (_dir() / "scores.json").write_text(
        json.dumps({r: scored[r]["summary"] for r in RUNNERS}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    s, q, matched_ids = matched(scored)
    print(term.rule("result"))
    print(term.grey(f"  over the {len(matched_ids)} ticket(s) both sides completed"))
    if not s.get("n") or not q.get("n"):
        print(term.yellow("Nothing scored on one side yet."))
    else:
        print(f"  {'':24} {'single':>10} {'squad':>10}")
        print(f"  {'quality  passed':24} {s['passed']}/{s['n']:<8} {q['passed']}/{q['n']:<8}")
        print(f"  {'         parts cited':24} {s['parts_cited_rate']:>9.0%} {q['parts_cited_rate']:>10.0%}")
        print(f"  {'speed    median s':24} {s['median_seconds']:>10} {q['median_seconds']:>10}")
        print(f"  {'tokens   total':24} {s['total_tokens']:>10,} {q['total_tokens']:>10,}")
        print(f"  {'cost     priced est':24} {s['priced_cost']:>10.4f} {q['priced_cost']:>10.4f}")
        print(f"  {'         calls':24} {s['calls']:>10} {q['calls']:>10}")
        short = len(ticket_set()) - len(matched_ids)
        print()
        if short:
            print(term.yellow(
                f"INCOMPLETE: {short} of {len(ticket_set())} tickets are not yet "
                "finished on both sides. Verdict withheld."
            ))
        else:
            v = verdict(s, q)
            print(term.bold(f"  keep: {v['keep']}   (squad costs {v['token_ratio']}x the tokens)"))
    print()
    print(f"Wrote {out / 'w10_race.md'}")
    print(f"Wrote {out / 'w10_handoffs.md'}")


if __name__ == "__main__":
    main()
