"""The one command. Score every case, then compare two runs.

    python -m evals.run_evals --tag before
    python -m evals.run_evals --tag after
    python -m evals.run_evals --compare before after

WHAT A RUN DOES
    For all 60 pool cases: generate an answer, apply the free assertion checks,
    and judge the answered ones on faithfulness and relevancy. Everything is
    cached, so a repeat run costs nothing and an interrupted run resumes.

WHY A RUN IS TAGGED
    Week 5 named the confound: the generation model is a free tier and this
    project already had to change model once mid-project. So a before-number
    carried over from another day is not a baseline.

    Every run therefore records the model, the prompt fingerprint and the
    corpus fingerprint. `--compare` REFUSES to report a delta when the two runs
    disagree on anything except the prompt, because that is the one thing the
    change is allowed to move.

WHAT COSTS MONEY
    One generation call per case, plus one judge call per answered case. Around
    113 calls for a full fresh run of 60 cases. Both layers are cached to disk.
    `--no-judge` runs the free assertion layer alone.
"""
from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict
from pathlib import Path

from config import STRATEGY_STRUCTURED, get_settings
from evals.w5_questions import W5_K
from evals.w5_trace import trace_config
from evals.w6_cases import eval_set, regression_verdict
from evals.w6_checks import FAILURE_MODES, aggregate, run_checks
from evals.w6_judge import (
    JUDGE_PROMPT_VERSION,
    JudgeCache,
    cited_sources,
    judge_answer,
    summarise,
)
from rag import term
from rag.answerer import answer_question

RUNS_DIR = "w6_runs"

# Settings that must match between two runs for a delta to mean anything.
# prompt_sha is excluded on purpose: it is the thing under test.
COMPARABLE_KEYS = (
    "strategy",
    "retrieval_mode",
    "k",
    "embedding_model",
    "chunk_count",
    "corpus_sha",
    "llm_model",
    "llm_temperature",
)


def _runs_dir() -> Path:
    path = Path(get_settings().results_dir) / RUNS_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _answer_cache_path(tag: str) -> Path:
    return _runs_dir() / f"{tag}__answers.json"


def _config_path(tag: str) -> Path:
    return _runs_dir() / f"{tag}__config.json"


def pinned_config(tag: str, cases_generated: bool) -> dict:
    """The settings that actually produced this run's answers.

    Pinned to the FIRST generation and never recomputed. Reading the live
    settings at report time is wrong: re-running a finished tag after changing
    a setting would silently restamp old answers with the new fingerprint, and
    the run would claim a provenance it does not have. That happened once, and
    it is exactly the kind of quiet corruption this whole project measures
    against.
    """
    path = _config_path(tag)
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    config = trace_config(STRATEGY_STRUCTURED, get_settings().retrieval_mode, W5_K)
    if cases_generated:
        path.write_text(json.dumps(config, indent=2, ensure_ascii=False), encoding="utf-8")
    return config


def _load_answer_cache(tag: str) -> dict:
    path = _answer_cache_path(tag)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


class _ReplayedAnswer:
    """A cached answer, shaped like the real Answer object the checks expect."""

    class _Cite:
        def __init__(self, d: dict) -> None:
            self.chunk_id = d["chunk_id"]
            self.resolves = d["resolves"]
            self.was_in_context = d.get("was_in_context", True)
            self.article_id = d.get("article_id")
            self.source_file = d.get("source_file")
            self.text = d.get("text")

    def __init__(self, d: dict) -> None:
        self.question = d["question"]
        self.answer = d["answer"]
        self.refused = d["refused"]
        self.gate_fired = d.get("gate_fired", False)
        self.retrieved = d.get("retrieved", [])
        self.citations = [self._Cite(c) for c in d.get("citations", [])]
        self.budget_degraded = d.get("budget_degraded", False)


def _serialise(answer) -> dict:
    return {
        "question": answer.question,
        "answer": answer.answer,
        "refused": answer.refused,
        "gate_fired": answer.gate_fired,
        "budget_degraded": getattr(answer, "budget_degraded", False),
        "retrieved": answer.retrieved,
        "citations": [
            {
                "chunk_id": c.chunk_id,
                "resolves": c.resolves,
                "was_in_context": c.was_in_context,
                "article_id": c.article_id,
                "source_file": c.source_file,
                "text": c.text,
            }
            for c in answer.citations
        ],
    }


# ---------------------------------------------------------------------------
# Running
# ---------------------------------------------------------------------------
def run(tag: str, *, use_judge: bool, limit: int | None, refresh: bool) -> dict:
    settings = get_settings()
    cases = eval_set()
    if limit:
        cases = cases[:limit]

    answers = {} if refresh else _load_answer_cache(tag)
    judge_cache = JudgeCache(_runs_dir() / f"{tag}__judge.json")
    answer_path = _answer_cache_path(tag)

    scores, judgements, rows = [], [], []
    generated_any = False
    started = time.time()

    for case in cases:
        cached = answers.get(case["id"])
        if cached is None:
            try:
                live = answer_question(
                    case["question"], STRATEGY_STRUCTURED, k=W5_K, use_gate=True
                )
                cached = _serialise(live)
                answers[case["id"]] = cached
                answer_path.write_text(
                    json.dumps(answers, indent=2, ensure_ascii=False), encoding="utf-8"
                )
            except Exception as exc:
                print(term.red(f"   {case['id']:<5} generation failed: {str(exc)[:70]}"))
                continue
            was_cached = False
            generated_any = True
        else:
            was_cached = True

        answer = _ReplayedAnswer(cached)
        score = run_checks(case, answer)
        scores.append(score)

        judgement = None
        if use_judge and not answer.refused:
            judgement = judge_answer(case, answer, cache=judge_cache)
            judgements.append(judgement)

        verdict = regression_verdict(case, score.failure_modes)
        rows.append(
            {
                "case_id": case["id"],
                "kind": case["kind"],
                "expected": case["expected_behaviour"],
                "is_regression": case["is_regression"],
                "regression_trace": case["regression_trace"],
                "banned_mode": case["banned_mode"],
                "regression_verdict": verdict,
                "passed": score.passed,
                "assertion_score": round(score.score, 4),
                "failure_modes": score.failure_modes,
                "checks": [asdict(c) for c in score.checks],
                "judge": judgement.as_dict() if judgement and judgement.usable else None,
                "refused": answer.refused,
                "answer": answer.answer,
                # Kept so the judge-validation worksheet can show a human the
                # exact text the judge was shown, without a second lookup.
                "cited_sources": cited_sources(answer),
                "cached_generation": was_cached,
            }
        )

        mark = term.green("pass") if score.passed else term.red(",".join(score.failure_modes))
        note = term.grey(" (cached)") if was_cached else ""
        print(f"   {case['id']:<5}{case['kind']:<15}{mark}{note}")

    summary = aggregate(scores)
    # A partial run must never be mistaken for a result. Week 4 learned this the
    # hard way: a report reading "6/13, 46.2%" looks like an eval score, when 47
    # of the 60 cases simply never ran.
    summary["attempted"] = len(cases)
    summary["not_run"] = len(cases) - len(scores)
    summary["complete"] = len(scores) == len(cases)
    summary["not_run_ids"] = sorted(
        {c["id"] for c in cases} - {s.case_id for s in scores}
    )
    if use_judge:
        summary["judge"] = summarise(judgements)

    regressions = [r for r in rows if r["is_regression"]]
    summary["regressions"] = {
        "total": len(regressions),
        "held": sum(1 for r in regressions if r["regression_verdict"] == "held"),
        "recurred": [r["case_id"] for r in regressions if r["regression_verdict"] == "recurred"],
        "new_break": [r["case_id"] for r in regressions if r["regression_verdict"] == "new_break"],
    }

    return {
        "tag": tag,
        "judge_prompt_version": JUDGE_PROMPT_VERSION if use_judge else None,
        "used_judge": use_judge,
        "config": pinned_config(tag, generated_any),
        "elapsed_s": round(time.time() - started, 1),
        "summary": summary,
        "rows": rows,
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def write_run_report(report: dict, path: Path) -> None:
    s = report["summary"]
    cfg = report["config"]
    lines = [
        f"# Week 6 eval run: `{report['tag']}`",
        "",
    ]
    if not s.get("complete", True):
        lines += [
            f"> **INCOMPLETE RUN. {s['not_run']} of {s['attempted']} cases never ran.**",
            "> Generation failed for them, so they are absent from every number",
            "> below. The percentages are over the cases that DID run, not over",
            "> the eval set. This is not a result yet.",
            "",
            f"> Not run: {', '.join(s['not_run_ids'])}",
            "",
            "> Re-run `python -m evals.run_evals --tag "
            f"{report['tag']}` to fill them in. Completed cases are cached and",
            "> are not charged again.",
            "",
        ]
    lines += [
        f"- Cases scored: {s['cases']} of {s.get('attempted', s['cases'])}",
        f"- Passed every applicable assertion: **{s['passed']}/{s['cases']}** "
        f"({s['pass_rate'] * 100:.1f}%)",
        f"- Mean assertion score: {s['mean_assertion_score']}",
        "",
        "## Run fingerprint",
        "",
        "| Setting | Value |",
        "|---|---|",
    ]
    for key in COMPARABLE_KEYS + ("prompt_sha",):
        lines.append(f"| {key} | `{cfg.get(key)}` |")

    lines += ["", "## Pass rate by problem type", "", "| Kind | Passed | Rate |", "|---|---|---|"]
    for kind, row in s["by_kind"].items():
        lines.append(f"| {kind} | {row['passed']}/{row['n']} | {row['pass_rate'] * 100:.0f}% |")

    lines += ["", "## Failure modes", "", "| Mode | Count |", "|---|---|"]
    for mode in FAILURE_MODES:
        lines.append(f"| {mode} | {s['failure_modes'].get(mode, 0)} |")

    reg = s["regressions"]
    lines += [
        "",
        "## Regressions from Week 5",
        "",
        f"- Pinned: {reg['total']}",
        f"- Held: {reg['held']}",
        f"- Recurred: {', '.join(reg['recurred']) if reg['recurred'] else 'none'}",
        f"- Broke a new way: {', '.join(reg['new_break']) if reg['new_break'] else 'none'}",
        "",
    ]

    if report.get("used_judge") and "judge" in s:
        j = s["judge"]
        lines += [
            "## Judge",
            "",
            "> These numbers mean nothing until `w6_validate_judge.py` shows the",
            "> judge agreeing with hand grading.",
            "",
            f"- Judged: {j['judged']}, not judged: {j['not_judged']}",
            f"- Faithful: {j['faithful']}/{j['judged']} ({j['faithful_rate'] * 100:.0f}%)",
            f"- Relevant: {j['relevant']}/{j['judged']} ({j['relevant_rate'] * 100:.0f}%)",
            f"- Unfaithful: {', '.join(j['unfaithful_ids']) or 'none'}",
            f"- Irrelevant: {', '.join(j['irrelevant_ids']) or 'none'}",
            "",
        ]

    lines += ["## Failing cases", "", "| Case | Kind | Failure modes |", "|---|---|---|"]
    for row in report["rows"]:
        if not row["passed"]:
            lines.append(
                f"| {row['case_id']} | {row['kind']} | {', '.join(row['failure_modes'])} |"
            )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def compare(before: dict, after: dict) -> dict:
    """Delta between two runs, refusing to report one that is not comparable."""
    b_cfg, a_cfg = before["config"], after["config"]
    mismatches = {
        key: (b_cfg.get(key), a_cfg.get(key))
        for key in COMPARABLE_KEYS
        if b_cfg.get(key) != a_cfg.get(key)
    }
    prompt_changed = b_cfg.get("prompt_sha") != a_cfg.get("prompt_sha")

    b, a = before["summary"], after["summary"]
    kinds = sorted(set(b["by_kind"]) | set(a["by_kind"]))
    incomplete = [
        tag
        for tag, summary in ((before["tag"], b), (after["tag"], a))
        if not summary.get("complete", True)
    ]
    return {
        "comparable": not mismatches and not incomplete,
        "incomplete_runs": incomplete,
        "mismatches": mismatches,
        "prompt_changed": prompt_changed,
        "pass_rate": {"before": b["pass_rate"], "after": a["pass_rate"]},
        "passed": {"before": b["passed"], "after": a["passed"], "n": b["cases"]},
        "by_kind": {
            kind: {
                "before": b["by_kind"].get(kind, {}).get("passed", 0),
                "after": a["by_kind"].get(kind, {}).get("passed", 0),
                "n": (b["by_kind"].get(kind) or a["by_kind"].get(kind, {})).get("n", 0),
            }
            for kind in kinds
        },
        "failure_modes": {
            mode: {
                "before": b["failure_modes"].get(mode, 0),
                "after": a["failure_modes"].get(mode, 0),
            }
            for mode in FAILURE_MODES
        },
        "regressions": {"before": b["regressions"], "after": a["regressions"]},
    }


def write_comparison(delta: dict, before: dict, after: dict, path: Path) -> None:
    n = delta["passed"]["n"]
    lines = [
        "# Week 6: before and after, per problem type",
        "",
        f"- before: `{before['tag']}`   after: `{after['tag']}`",
        f"- Prompt changed between runs: **{delta['prompt_changed']}**",
        "",
    ]
    if delta.get("incomplete_runs"):
        lines += [
            "> **NOT COMPARABLE.** These runs did not finish: "
            f"{', '.join(delta['incomplete_runs'])}.",
            "> A delta between two partial runs compares different sets of cases.",
            "> Finish both runs first.",
            "",
        ]
    if delta["mismatches"]:
        lines += [
            "> **NOT COMPARABLE.** These two runs differ on a setting that is not",
            "> the thing under test, so the delta below is not attributable.",
            "",
            "| Setting | before | after |",
            "|---|---|---|",
        ]
        for key, (b, a) in delta["mismatches"].items():
            lines.append(f"| {key} | `{b}` | `{a}` |")
        lines.append("")
    elif not delta["prompt_changed"]:
        lines += [
            "> **Note:** the prompt fingerprint is identical in both runs, so this",
            "> is a repeatability check rather than a before/after.",
            "",
        ]

    pb, pa = delta["passed"]["before"], delta["passed"]["after"]
    lines += [
        "## Headline",
        "",
        "| | passed | rate |",
        "|---|---|---|",
        f"| before | {pb}/{n} | {delta['pass_rate']['before'] * 100:.1f}% |",
        f"| after | {pa}/{n} | {delta['pass_rate']['after'] * 100:.1f}% |",
        f"| change | **{pa - pb:+d}** | "
        f"{(delta['pass_rate']['after'] - delta['pass_rate']['before']) * 100:+.1f} pts |",
        "",
        "## By problem type",
        "",
        "| Kind | before | after | change |",
        "|---|---|---|---|",
    ]
    for kind, row in delta["by_kind"].items():
        change = row["after"] - row["before"]
        lines.append(
            f"| {kind} | {row['before']}/{row['n']} | {row['after']}/{row['n']} "
            f"| {change:+d} |"
        )

    lines += ["", "## By failure mode", "", "| Mode | before | after | change |", "|---|---|---|---|"]
    for mode, row in delta["failure_modes"].items():
        change = row["after"] - row["before"]
        arrow = "**better**" if change < 0 else ("worse" if change > 0 else "")
        lines.append(f"| {mode} | {row['before']} | {row['after']} | {change:+d} {arrow} |")

    rb, ra = delta["regressions"]["before"], delta["regressions"]["after"]
    lines += [
        "",
        "## Week 5 regressions",
        "",
        "| | before | after |",
        "|---|---|---|",
        f"| held | {rb['held']}/{rb['total']} | {ra['held']}/{ra['total']} |",
        f"| recurred | {', '.join(rb['recurred']) or 'none'} | {', '.join(ra['recurred']) or 'none'} |",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
def main() -> None:
    term.init()
    parser = argparse.ArgumentParser(description="Week 6 eval set.")
    parser.add_argument("--tag", help="Label this run, e.g. before or after.")
    parser.add_argument("--compare", nargs=2, metavar=("BEFORE", "AFTER"))
    parser.add_argument("--no-judge", action="store_true", help="Assertions only, no API cost.")
    parser.add_argument("--limit", type=int, help="Score only the first N cases.")
    parser.add_argument("--refresh", action="store_true", help="Ignore cached generations.")
    args = parser.parse_args()

    out = Path(get_settings().results_dir)

    if args.compare:
        before_tag, after_tag = args.compare
        try:
            before = json.loads((_runs_dir() / f"{before_tag}.json").read_text(encoding="utf-8"))
            after = json.loads((_runs_dir() / f"{after_tag}.json").read_text(encoding="utf-8"))
        except OSError as exc:
            print(term.red(f"Cannot load both runs: {exc}"))
            raise SystemExit(1)
        delta = compare(before, after)
        write_comparison(delta, before, after, out / "w6_before_after.md")
        (_runs_dir() / "comparison.json").write_text(
            json.dumps(delta, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        pb, pa = delta["passed"]["before"], delta["passed"]["after"]
        print()
        if not delta["comparable"]:
            print(term.paint("NOT COMPARABLE", "red", "bold"), delta["mismatches"])
        print(f"pass: {pb}/{delta['passed']['n']} -> {pa}/{delta['passed']['n']}  ({pa - pb:+d})")
        print(f"Wrote {out / 'w6_before_after.md'}")
        return

    if not args.tag:
        parser.error("give --tag NAME to run, or --compare BEFORE AFTER")

    print(term.bold(f"\n-- scoring the eval set, tag={args.tag}"))
    report = run(
        args.tag,
        use_judge=not args.no_judge,
        limit=args.limit,
        refresh=args.refresh,
    )
    (_runs_dir() / f"{args.tag}.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    write_run_report(report, out / f"w6_run_{args.tag}.md")

    s = report["summary"]
    print()
    print(term.bold(f"{'kind':<16}{'passed':<10}{'rate':<8}"))
    print("-" * 34)
    for kind, row in s["by_kind"].items():
        cell = f"{row['passed']}/{row['n']}"
        colour = term.green if row["pass_rate"] == 1.0 else term.yellow
        print(f"{kind:<16}{colour(f'{cell:<10}')}{row['pass_rate'] * 100:>5.0f}%")
    print("-" * 34)
    print(f"{'TOTAL':<16}{s['passed']}/{s['cases']}{'':<5}{s['pass_rate'] * 100:>5.1f}%")
    print()
    print(term.bold("failure modes"))
    for mode in FAILURE_MODES:
        count = s["failure_modes"].get(mode, 0)
        if count:
            print(f"  {term.red(str(count)):<4} {mode}")
    reg = s["regressions"]
    print()
    print(f"week 5 regressions held: {reg['held']}/{reg['total']}"
          + (f"  recurred: {reg['recurred']}" if reg["recurred"] else ""))
    print(f"\nWrote {out / f'w6_run_{args.tag}.md'}")


if __name__ == "__main__":
    main()
