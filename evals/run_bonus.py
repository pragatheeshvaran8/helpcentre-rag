"""Bonus challenge: precision that costs completeness.

The question has three parts. Two are answered by a single row of the invoice
error table. The third is answered only by article PROSE, several paragraphs
away from that table:

    "A reissued invoice keeps the original invoice number and gains a revision
     suffix, such as EU-2026-0004417-R2."

Prediction, written into evals/questions.py before this was ever run: the
structure-aware chunker retrieves the tight table row precisely and then has no
prose in context, so it cannot complete the answer. The baseline chunker cuts on
character count, so its chunks blend prose and table, and it may carry the
numbering sentence along by accident.

Run:  python -m evals.run_bonus
"""
from __future__ import annotations

import json
from pathlib import Path

from config import STRATEGIES, get_settings
from evals.questions import BONUS_QUESTION
from rag.answerer import answer_question

# Literal evidence for each part of the answer. Used to score completeness
# objectively rather than by eye.
PART_EVIDENCE = {
    "meaning": ["legacy tax code"],
    "fix": ["reissue"],
    "numbering": ["revision suffix"],
}


def score_parts(text: str) -> dict:
    low = text.lower()
    return {
        part: all(ev.lower() in low for ev in evidence)
        for part, evidence in PART_EVIDENCE.items()
    }


# Two retrieval budgets. k=5 is the budget used everywhere else in this
# write-up. k=1 is the tight budget, where a chunker's precision and its
# completeness pull hardest against each other.
BUDGETS = (5, 1)


def run_one(question: str, strategy: str, k: int) -> dict:
    ans = answer_question(question, strategy, k=k, use_gate=True)
    parts = score_parts(ans.answer)
    return {
        "k": k,
        "strategy": strategy,
        "answer": ans.answer,
        "refused": ans.refused,
        "parts_answered": parts,
        "parts_score": sum(parts.values()),
        "err4032_row_retrieved": any("err-4032" in h["text"].lower() for h in ans.retrieved),
        "numbering_prose_retrieved": any(
            "revision suffix" in h["text"].lower() for h in ans.retrieved
        ),
        "retrieved": [
            {
                "rank": h["rank"],
                "score": h["score"],
                "chunk_id": h["chunk_id"],
                "article_id": h["article_id"],
                "char_len": h["char_len"],
                "has_err4032": "err-4032" in h["text"].lower(),
                "has_numbering_prose": "revision suffix" in h["text"].lower(),
            }
            for h in ans.retrieved
        ],
        "citations": [c.chunk_id for c in ans.citations],
    }


def run() -> dict:
    q = BONUS_QUESTION["question"]
    runs: dict[str, dict] = {}
    for k in BUDGETS:
        for strategy in STRATEGIES:
            print(f"  generating bonus / {strategy} / k={k} ...")
            runs[f"{strategy}_k{k}"] = run_one(q, strategy, k)
    return {"question": q, "budgets": list(BUDGETS), "runs": runs}


def write_report(result: dict, path: Path) -> None:
    runs = result["runs"]
    lines = [
        "# Bonus: precision against completeness",
        "",
        f"**Question:** {result['question']}",
        "",
        "Three parts. Parts 1 and 2 live in one row of the invoice error table",
        "in HC-4002. Part 3 lives in prose, in a different section of the same",
        "article, several paragraphs from that table.",
        "",
        "Run at two retrieval budgets. k=5 is the budget used everywhere else in",
        "this write-up. k=1 is the tight budget, where precision and completeness",
        "pull hardest against each other.",
        "",
        "## Summary",
        "",
        "| k | strategy | ERR-4032 row retrieved | numbering prose retrieved | parts answered | refused |",
        "|---|---|---|---|---|---|",
    ]
    for k in result["budgets"]:
        for strategy in STRATEGIES:
            d = runs[f"{strategy}_k{k}"]
            lines.append(
                f"| {k} | {strategy} | {'yes' if d['err4032_row_retrieved'] else 'no'} "
                f"| {'yes' if d['numbering_prose_retrieved'] else 'no'} "
                f"| {d['parts_score']}/3 | {d['refused']} |"
            )

    for k in result["budgets"]:
        lines += ["", f"## Retrieval budget k={k}", ""]
        for strategy in STRATEGIES:
            d = runs[f"{strategy}_k{k}"]
            parts = ", ".join(
                f"{p}={'yes' if v else 'no'}" for p, v in d["parts_answered"].items()
            )
            lines += [
                f"### k={k} / {strategy} - {d['parts_score']}/3 parts ({parts})",
                "",
                "```",
                d["answer"],
                "```",
                "",
                "`has_4032` = chunk holds the ERR-4032 row. "
                "`has_prose` = chunk holds the invoice-numbering sentence.",
                "",
                "| rank | score | chunk_id | chars | has_4032 | has_prose |",
                "|---|---|---|---|---|---|",
            ]
            for h in d["retrieved"]:
                lines.append(
                    f"| {h['rank']} | {h['score']:.4f} | `{h['chunk_id']}` | {h['char_len']} "
                    f"| {'yes' if h['has_err4032'] else 'no'} "
                    f"| {'yes' if h['has_numbering_prose'] else 'no'} |"
                )
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    settings = get_settings()
    out = Path(settings.results_dir)
    result = run()
    write_report(result, out / "bonus.md")
    (out / "bonus.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print()
    print(f"{'run':<20}{'parts':<8}{'refused':<10}{'4032':<8}{'prose':<8}")
    print("-" * 54)
    for name, data in result["runs"].items():
        print(
            f"{name:<20}{str(data['parts_score']) + '/3':<8}"
            f"{str(data['refused']):<10}{str(data['err4032_row_retrieved']):<8}"
            f"{str(data['numbering_prose_retrieved']):<8}"
        )
    print()
    print(f"Wrote {out / 'bonus.md'}")


if __name__ == "__main__":
    main()
