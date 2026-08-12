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


def run() -> dict:
    q = BONUS_QUESTION["question"]
    results = {}
    for strategy in STRATEGIES:
        print(f"  generating bonus / {strategy} ...")
        ans = answer_question(q, strategy, use_gate=True)
        parts = score_parts(ans.answer)
        # Did the prose sentence reach the model at all?
        prose_in_context = any(
            "revision suffix" in h["text"].lower() for h in ans.retrieved
        )
        table_row_in_context = any(
            "err-4032" in h["text"].lower() for h in ans.retrieved
        )
        results[strategy] = {
            "answer": ans.answer,
            "refused": ans.refused,
            "parts_answered": parts,
            "parts_score": sum(parts.values()),
            "err4032_row_retrieved": table_row_in_context,
            "numbering_prose_retrieved": prose_in_context,
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
    return {"question": q, "by_strategy": results}


def write_report(result: dict, path: Path) -> None:
    b = result["by_strategy"]["baseline"]
    s = result["by_strategy"]["structured"]
    lines = [
        "# Bonus: the structure-aware chunker retrieves better and answers worse",
        "",
        f"**Question:** {result['question']}",
        "",
        "Three parts. Parts 1 and 2 live in one row of the invoice error table.",
        "Part 3 lives in article prose, in a different section of HC-4002.",
        "",
        "## Side by side",
        "",
        "| | baseline | structured |",
        "|---|---|---|",
        f"| ERR-4032 row retrieved | {b['err4032_row_retrieved']} | {s['err4032_row_retrieved']} |",
        f"| numbering prose retrieved | {b['numbering_prose_retrieved']} "
        f"| {s['numbering_prose_retrieved']} |",
        f"| parts answered | {b['parts_score']}/3 | {s['parts_score']}/3 |",
        f"| refused | {b['refused']} | {s['refused']} |",
        "",
        "Part-by-part:",
        "",
        "| Part | baseline | structured |",
        "|---|---|---|",
    ]
    for part in PART_EVIDENCE:
        lines.append(
            f"| {part} | {'yes' if b['parts_answered'][part] else 'no'} "
            f"| {'yes' if s['parts_answered'][part] else 'no'} |"
        )

    for name, data in (("baseline", b), ("structured", s)):
        lines += [
            "",
            f"## Answer - {name}",
            "",
            "```",
            data["answer"],
            "```",
            "",
            f"Retrieved (k=5), `has_4032` = chunk holds the ERR-4032 row, "
            f"`has_prose` = chunk holds the numbering sentence:",
            "",
            "| rank | score | chunk_id | chars | has_4032 | has_prose |",
            "|---|---|---|---|---|---|",
        ]
        for h in data["retrieved"]:
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
    for strategy, data in result["by_strategy"].items():
        print(
            f"{strategy:<12} parts={data['parts_score']}/3  refused={data['refused']}  "
            f"err4032_retrieved={data['err4032_row_retrieved']}  "
            f"prose_retrieved={data['numbering_prose_retrieved']}"
        )
    print()
    print(f"Wrote {out / 'bonus.md'}")


if __name__ == "__main__":
    main()
