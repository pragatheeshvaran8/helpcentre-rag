"""Validate the judge against hand grading, before any judge number is quoted.

THE MENTOR CHECKLIST ASKS THIS DIRECTLY
    "If they used an AI judge, did they check it agrees with their own grading
    first?"

    An unvalidated judge is a confident number nobody has any reason to trust.
    It is worse than no number, because a number gets repeated.

HOW IT WORKS
    1. python -m evals.w6_validate_judge --sample 20 --run before
         Writes a worksheet. You grade it yourself, by hand, from the answer and
         the source text. Two yes/no columns, nothing else.

    2. python -m evals.w6_validate_judge --score --run before
         Compares your grades to the judge's and reports agreement and Cohen's
         kappa per dimension, then says whether the judge may be trusted.

WHY THE SAMPLE IS STRATIFIED, NOT RANDOM
    A random sample of a mostly-passing set is nearly all yeses. Agreement then
    looks excellent while telling you nothing about the case that matters: the
    one where the judge says "unfaithful" and is wrong, or says "faithful" and
    is wrong.

    So every case the judge marked NO is included, plus a spread of cases it
    marked YES. That deliberately over-samples disagreement candidates. It
    measures whether the judge can be trusted where it actually bites.

WHY COHEN'S KAPPA AND NOT JUST AGREEMENT
    If 90% of answers are faithful, a judge that says "faithful" every single
    time scores 90% agreement while being useless. Kappa subtracts the
    agreement you would get by chance, so a rubber-stamp judge scores near 0.

THE BAR
    Agreement of 80% or more AND kappa of 0.6 or more, on each dimension.
    Below that the judge's numbers are not reported as findings.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
from pathlib import Path

from config import get_settings
from evals.w5_questions import POOL_BY_ID
from rag import term

WORKSHEET_CSV = "w6_judge_worksheet.csv"
WORKSHEET_MD = "w6_judge_worksheet.md"

MIN_AGREEMENT = 0.80
MIN_KAPPA = 0.60

# Fixed so a worksheet can be regenerated identically.
SAMPLE_SEED = 20260826


def _runs_dir() -> Path:
    return Path(get_settings().results_dir) / "w6_runs"


def _load_run(tag: str) -> dict:
    path = _runs_dir() / f"{tag}.json"
    if not path.exists():
        raise SystemExit(f"No run tagged {tag!r}. Run: python -m evals.run_evals --tag {tag}")
    return json.loads(path.read_text(encoding="utf-8"))


def stratified_sample(rows: list[dict], size: int) -> list[dict]:
    """Every judge NO, plus a spread of judge YES, up to ``size``."""
    judged = [r for r in rows if r.get("judge")]
    says_no = [r for r in judged if not (r["judge"]["faithful"] and r["judge"]["relevant"])]
    says_yes = [r for r in judged if r["judge"]["faithful"] and r["judge"]["relevant"]]

    rng = random.Random(SAMPLE_SEED)
    rng.shuffle(says_yes)
    take_yes = max(size - len(says_no), 0)
    chosen = says_no + says_yes[:take_yes]
    chosen.sort(key=lambda r: r["case_id"])
    return chosen


def write_worksheet(rows: list[dict], run_tag: str, out: Path) -> None:
    """Two files: a CSV to fill in, and a markdown copy to read from."""
    csv_path = out / WORKSHEET_CSV
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["case_id", "kind", "faithful_human", "relevant_human", "note", "question"]
        )
        for row in rows:
            writer.writerow(
                [row["case_id"], row["kind"], "", "", "", POOL_BY_ID[row["case_id"]]["question"]]
            )

    lines = [
        f"# Judge validation worksheet, run `{run_tag}`",
        "",
        f"{len(rows)} cases to grade by hand. Fill `faithful_human` and",
        f"`relevant_human` in [{WORKSHEET_CSV}]({WORKSHEET_CSV}) with **y** or **n**.",
        "",
        "Grade from the answer and the source text below, nothing else. Do not",
        "look at the judge's verdict first. It is deliberately not shown here.",
        "",
        "- **faithful** — does the answer say ONLY what the sources say?",
        "- **relevant** — does it answer the question that was actually asked?",
        "",
        "---",
        "",
    ]
    for row in rows:
        question = POOL_BY_ID[row["case_id"]]["question"]
        lines += [
            f"## {row['case_id']}  ({row['kind']})",
            "",
            f"**Question:** {question}",
            "",
            "**Answer:**",
            "",
            "```",
            row["answer"].strip(),
            "```",
            "",
            "**Sources it cited:**",
            "",
        ]
        sources = row.get("cited_sources")
        if sources:
            lines += ["```", sources.strip(), "```", ""]
        else:
            lines += ["_(see the run json for the full cited chunk text)_", ""]
        lines += ["| faithful (y/n) | relevant (y/n) | note |", "|---|---|---|", "|  |  |  |", ""]
    (out / WORKSHEET_MD).write_text("\n".join(lines), encoding="utf-8")


def read_worksheet(path: Path) -> dict[str, dict]:
    """Read the human grades back. Blank rows are treated as not graded."""
    if not path.exists():
        raise SystemExit(f"No worksheet at {path}. Run --sample first.")
    graded: dict[str, dict] = {}
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            faithful = (row.get("faithful_human") or "").strip().lower()
            relevant = (row.get("relevant_human") or "").strip().lower()
            if faithful in ("y", "n") and relevant in ("y", "n"):
                graded[row["case_id"]] = {
                    "faithful": faithful == "y",
                    "relevant": relevant == "y",
                    "note": (row.get("note") or "").strip(),
                }
    return graded


def cohens_kappa(human: list[bool], judge: list[bool]) -> float | None:
    """Agreement above chance. 0 means no better than guessing the base rate.

    Returns None when one side never varies. With all-yes or all-no on a
    dimension there is no chance-corrected agreement to compute: every
    definition divides by zero. Reporting 1.0 there would be a lie dressed as a
    perfect score, so the caller is told the number does not exist instead.
    """
    n = len(human)
    if n == 0:
        return None
    if len(set(human)) < 2 or len(set(judge)) < 2:
        return None
    observed = sum(1 for h, j in zip(human, judge) if h == j) / n
    h_yes, j_yes = sum(human) / n, sum(judge) / n
    expected = h_yes * j_yes + (1 - h_yes) * (1 - j_yes)
    if expected >= 1.0:
        return None
    return (observed - expected) / (1 - expected)


def compare(graded: dict[str, dict], rows: list[dict]) -> dict:
    by_id = {r["case_id"]: r for r in rows if r.get("judge")}
    pairs = [(cid, g, by_id[cid]["judge"]) for cid, g in graded.items() if cid in by_id]

    out: dict = {"n": len(pairs), "dimensions": {}, "disagreements": []}
    for dim in ("faithful", "relevant"):
        human = [g[dim] for _, g, _ in pairs]
        judge = [bool(j[dim]) for _, _, j in pairs]
        agree = sum(1 for h, j in zip(human, judge) if h == j)
        kappa = cohens_kappa(human, judge)
        agreement = agree / len(pairs) if pairs else 0.0
        no_variance = kappa is None
        out["dimensions"][dim] = {
            "n": len(pairs),
            "agreed": agree,
            "agreement": round(agreement, 4),
            "kappa": round(kappa, 4) if kappa is not None else None,
            "kappa_undefined": no_variance,
            "human_yes": sum(human),
            "judge_yes": sum(judge),
            # Without variance, kappa cannot be computed, so the dimension
            # cannot clear the bar however high the raw agreement looks.
            "trustworthy": (not no_variance)
            and agreement >= MIN_AGREEMENT
            and kappa >= MIN_KAPPA,
        }

    for cid, human, judge in pairs:
        for dim in ("faithful", "relevant"):
            if human[dim] != bool(judge[dim]):
                out["disagreements"].append(
                    {
                        "case_id": cid,
                        "dimension": dim,
                        "human": human[dim],
                        "judge": bool(judge[dim]),
                        "judge_reason": judge.get(f"{dim}_reason", ""),
                        "human_note": human.get("note", ""),
                    }
                )

    out["verdict"] = (
        "trust"
        if all(d["trustworthy"] for d in out["dimensions"].values()) and out["n"] >= 10
        else "do not trust"
    )
    return out


def write_report(result: dict, run_tag: str, path: Path) -> None:
    lines = [
        f"# Judge validation against hand grading, run `{run_tag}`",
        "",
        f"- Cases graded by hand: **{result['n']}**",
        f"- Bar: agreement >= {MIN_AGREEMENT:.0%} AND Cohen's kappa >= {MIN_KAPPA}",
        f"- Verdict: **{result['verdict'].upper()}**",
        "",
        "## Agreement per dimension",
        "",
        "| Dimension | Agreed | Agreement | Kappa | Human yes | Judge yes | Trustworthy |",
        "|---|---|---|---|---|---|---|",
    ]
    for dim, d in result["dimensions"].items():
        kappa_cell = (
            "**n/a, no variance**" if d.get("kappa_undefined") else str(d["kappa"])
        )
        lines.append(
            f"| {dim} | {d['agreed']}/{d['n']} | {d['agreement'] * 100:.0f}% | {kappa_cell} "
            f"| {d['human_yes']} | {d['judge_yes']} | {'yes' if d['trustworthy'] else '**no**'} |"
        )

    lines += [
        "",
        "Kappa matters more than raw agreement here. If most answers are",
        "faithful, a judge that always says yes still scores high agreement.",
        "Kappa subtracts that free credit.",
        "",
        "## Where we disagreed",
        "",
    ]
    if not result["disagreements"]:
        lines.append("_No disagreements._")
    else:
        lines += [
            "| Case | Dimension | Human | Judge | Judge's reason |",
            "|---|---|---|---|---|",
        ]
        for d in result["disagreements"]:
            lines.append(
                f"| {d['case_id']} | {d['dimension']} | {'yes' if d['human'] else 'no'} "
                f"| {'yes' if d['judge'] else 'no'} | {d['judge_reason'] or '-'} |"
            )
    lines += [
        "",
        "## What this licenses",
        "",
        (
            "The judge agrees with hand grading closely enough to quote. Its"
            " faithfulness and relevancy rates may be reported as findings."
            if result["verdict"] == "trust"
            else "**The judge is not validated.** Its numbers must not be quoted as"
            " findings. The assertion checks are unaffected: they are"
            " deterministic and need no judge."
        ),
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    term.init()
    parser = argparse.ArgumentParser(description="Validate the judge against hand grading.")
    parser.add_argument("--run", default="before", help="Which eval run to validate against.")
    parser.add_argument("--sample", type=int, help="Write a worksheet of this many cases.")
    parser.add_argument("--score", action="store_true", help="Score the filled worksheet.")
    args = parser.parse_args()

    out = Path(get_settings().results_dir)
    report = _load_run(args.run)
    rows = report["rows"]

    if args.sample:
        chosen = stratified_sample(rows, args.sample)
        if not chosen:
            raise SystemExit("No judged rows in that run. Run without --no-judge first.")
        write_worksheet(chosen, args.run, out)
        no_count = sum(
            1 for r in chosen if not (r["judge"]["faithful"] and r["judge"]["relevant"])
        )
        print(term.green(f"Wrote {out / WORKSHEET_CSV} with {len(chosen)} cases."))
        print(term.grey(f"  {no_count} of them are cases the judge marked NO."))
        print(term.grey(f"  Read {out / WORKSHEET_MD}, fill the CSV, then run --score."))
        return

    if not args.score:
        parser.error("give --sample N to create a worksheet, or --score to grade it")

    graded = read_worksheet(out / WORKSHEET_CSV)
    if not graded:
        raise SystemExit("No completed rows in the worksheet. Fill y/n in both columns.")
    result = compare(graded, rows)
    write_report(result, args.run, out / "w6_judge_validation.md")
    (_runs_dir() / f"{args.run}__validation.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print()
    print(term.bold(f"{'dimension':<12}{'agreement':<12}{'kappa':<10}{'trust':<8}"))
    print("-" * 42)
    for dim, d in result["dimensions"].items():
        colour = term.green if d["trustworthy"] else term.red
        kappa_cell = "n/a" if d.get("kappa_undefined") else str(d["kappa"])
        print(
            f"{dim:<12}{d['agreement'] * 100:>6.0f}%     {kappa_cell:<10}"
            f"{colour('yes' if d['trustworthy'] else 'NO')}"
        )
    print()
    verdict = result["verdict"]
    print(term.paint(f"VERDICT: {verdict.upper()}", "green" if verdict == "trust" else "red", "bold"))
    print(f"Wrote {out / 'w6_judge_validation.md'}")


if __name__ == "__main__":
    main()
