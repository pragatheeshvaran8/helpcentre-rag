"""Search-only evaluation: the SAME 8 questions against BOTH chunking strategies.

No LLM is involved anywhere in this file. This measures retrieval and nothing
else.

Hit rule (defined in evals/questions.py, fixed before any run):
    a question is a hit-in-top-5 when at least one of the 5 retrieved chunks
    has the expected article_id AND literally contains every must_contain
    string for that question.

Outputs:
    results/search_dump.md   full top-5 for all 8 questions under both
                             strategies, with scores and chunk text
    results/hit_matrix.md    the per-question hit record and the two X/8 numbers
    results/search_eval.json machine-readable version of the same run

Run:  python -m evals.run_search_eval
"""
from __future__ import annotations

import json
from pathlib import Path

from config import STRATEGIES, get_settings
from evals.questions import QUESTIONS
from rag.retriever import chunk_answers_question, format_hits, search


def evaluate_question(question: dict, strategy: str, k: int) -> dict:
    """Run one question against one strategy and decide hit or miss."""
    hits = format_hits(search(question["question"], strategy, k=k))

    hit_rank = None
    for h in hits:
        right_article = h["article_id"] == question["expected_article_id"]
        has_answer = chunk_answers_question(h["text"], question["must_contain"])
        h["right_article"] = right_article
        h["contains_answer"] = has_answer
        h["is_hit"] = right_article and has_answer
        if h["is_hit"] and hit_rank is None:
            hit_rank = h["rank"]

    # Diagnosis support: did we retrieve the right article but a chunk that
    # cannot answer? That is the table-splitting failure, and it is different
    # from retrieving the wrong article entirely.
    near_miss = hit_rank is None and any(h["right_article"] for h in hits)

    return {
        "question_id": question["id"],
        "strategy": strategy,
        "hit": hit_rank is not None,
        "hit_rank": hit_rank,
        "near_miss_right_article_wrong_chunk": near_miss,
        "top1_chunk_id": hits[0]["chunk_id"] if hits else None,
        "top1_score": hits[0]["score"] if hits else None,
        "hits": hits,
    }


def run() -> dict:
    settings = get_settings()
    k = settings.top_k
    records: list[dict] = []
    for question in QUESTIONS:
        for strategy in STRATEGIES:
            records.append(evaluate_question(question, strategy, k))

    totals = {
        s: sum(1 for r in records if r["strategy"] == s and r["hit"]) for s in STRATEGIES
    }
    return {
        "k": k,
        "embedding_model": settings.embedding_model,
        "distance_metric": settings.distance_metric,
        "chunk_size": settings.chunk_size,
        "chunk_overlap": settings.chunk_overlap,
        "n_questions": len(QUESTIONS),
        "totals": totals,
        "secondary": {s: secondary_metrics(records, s, k) for s in STRATEGIES},
        "records": records,
    }


def secondary_metrics(records: list[dict], strategy: str, k: int) -> dict:
    """Sharper lenses on the SAME run and the SAME 8 questions.

    hit-in-top-5 is the number the task asks for, but on a 6-article corpus
    top-5 is roughly 15% of the whole index, so it saturates easily. These
    metrics come from the identical retrieval run. No question was rewritten and
    nothing was re-searched to produce them.

    context_orphan_chunks is the one that matters most in practice: how many of
    the chunks actually handed to the model carry table data rows with no header
    row. Those chunks retrieve fine and then mislead generation.
    """
    subset = [r for r in records if r["strategy"] == strategy]
    n = len(subset)
    delivered = [h for r in subset for h in r["hits"]]
    orphans = [h for h in delivered if h["orphan_table_rows"]]
    return {
        "hit_at_1": sum(1 for r in subset if r["hit_rank"] == 1),
        "hit_at_5": sum(1 for r in subset if r["hit"]),
        "mrr": round(
            sum(1 / r["hit_rank"] for r in subset if r["hit_rank"]) / n, 4
        ),
        "chunks_delivered": len(delivered),
        "context_orphan_chunks": len(orphans),
        "context_orphan_rate": round(len(orphans) / len(delivered), 4) if delivered else 0.0,
        "questions_with_orphan_in_context": len(
            {h_r["question_id"] for h_r in subset if any(h["orphan_table_rows"] for h in h_r["hits"])}
        ),
    }


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------
def _record(records: list[dict], qid: str, strategy: str) -> dict:
    return next(r for r in records if r["question_id"] == qid and r["strategy"] == strategy)


def write_hit_matrix(report: dict, path: Path) -> None:
    recs = report["records"]
    lines = [
        "# Hit-in-top-5, same 8 questions, both chunking strategies",
        "",
        f"- Questions: {report['n_questions']}",
        f"- k = {report['k']} (top-5)",
        f"- Embedding model: `{report['embedding_model']}` (IDENTICAL for both runs)",
        f"- Distance: {report['distance_metric']}; target chunk size: {report['chunk_size']}",
        "- No relevance threshold is applied. A miss is a real retrieval miss.",
        "",
        "## Per-question record",
        "",
        "| Q | Type | Expected article | baseline hit | rank | structured hit | rank |",
        "|---|---|---|---|---|---|---|",
    ]
    for q in QUESTIONS:
        b = _record(recs, q["id"], "baseline")
        s = _record(recs, q["id"], "structured")
        lines.append(
            f"| {q['id']} | {q['type']} | {q['expected_article_id']} "
            f"| {'HIT' if b['hit'] else 'MISS'} | {b['hit_rank'] or '-'} "
            f"| {'HIT' if s['hit'] else 'MISS'} | {s['hit_rank'] or '-'} |"
        )

    totals = report["totals"]
    n = report["n_questions"]
    sec = report["secondary"]
    lines += [
        "",
        "## The two numbers",
        "",
        "| Chunking strategy | hit-in-top-5 |",
        "|---|---|",
        f"| baseline (RecursiveCharacterTextSplitter, 1000/150) | {totals['baseline']}/{n} |",
        f"| structured (table-row aware) | {totals['structured']}/{n} |",
        "",
        "## Secondary metrics, same run, same 8 questions",
        "",
        "hit-in-top-5 saturates on a 6-article corpus, because top-5 is about",
        "15% of the whole index. These come from the identical retrieval run.",
        "",
        "| Metric | baseline | structured |",
        "|---|---|---|",
        f"| hit-in-top-5 | {sec['baseline']['hit_at_5']}/{n} | {sec['structured']['hit_at_5']}/{n} |",
        f"| hit-in-top-1 | {sec['baseline']['hit_at_1']}/{n} | {sec['structured']['hit_at_1']}/{n} |",
        f"| mean reciprocal rank | {sec['baseline']['mrr']} | {sec['structured']['mrr']} |",
        f"| chunks delivered into context | {sec['baseline']['chunks_delivered']} "
        f"| {sec['structured']['chunks_delivered']} |",
        f"| of those, header-less table chunks | {sec['baseline']['context_orphan_chunks']} "
        f"| {sec['structured']['context_orphan_chunks']} |",
        f"| questions given a header-less chunk | "
        f"{sec['baseline']['questions_with_orphan_in_context']}/{n} "
        f"| {sec['structured']['questions_with_orphan_in_context']}/{n} |",
        "",
        "## Near misses",
        "",
        "A near miss means the right article was retrieved but the chunk could",
        "not answer the question. That is the table-splitting failure, and it is",
        "a different fault from retrieving the wrong article.",
        "",
        "| Q | strategy | near miss |",
        "|---|---|---|",
    ]
    for r in recs:
        if r["near_miss_right_article_wrong_chunk"]:
            lines.append(f"| {r['question_id']} | {r['strategy']} | yes |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def write_search_dump(report: dict, path: Path) -> None:
    recs = report["records"]
    lines = [
        "# Search-only dump: all 8 questions, both strategies, top-5 each",
        "",
        "No LLM was called to produce this file. Scores are cosine relevance",
        "(1 - cosine distance); higher is better.",
        "",
        "Legend: `HIT` = right article AND chunk contains the full answer.",
        "`hdr` = chunk retains a markdown table header row.",
        "`ORPHAN` = chunk carries table data rows but lost its header row.",
        "",
    ]
    for q in QUESTIONS:
        lines += [
            "---",
            "",
            f"## {q['id']} ({q['type']})",
            "",
            f"**Question:** {q['question']}",
            "",
            f"**Known-correct location:** `{q['expected_article_id']}` -> {q['expected_section']}",
            "",
            f"**Known answer:** {q['known_answer']}",
            "",
            f"**Hit requires the chunk to contain:** "
            + ", ".join(f"`{m}`" for m in q["must_contain"]),
            "",
        ]
        for strategy in STRATEGIES:
            r = _record(recs, q["id"], strategy)
            verdict = f"HIT at rank {r['hit_rank']}" if r["hit"] else "MISS"
            lines += [f"### {q['id']} / {strategy} -> {verdict}", ""]
            for h in r["hits"]:
                flags = []
                if h["is_hit"]:
                    flags.append("HIT")
                elif h["right_article"]:
                    flags.append("right-article-wrong-chunk")
                if h["orphan_table_rows"]:
                    flags.append("ORPHAN")
                elif h["has_table_header"]:
                    flags.append("hdr")
                flag_text = (" [" + ", ".join(flags) + "]") if flags else ""
                lines += [
                    f"**{h['rank']}. score {h['score']:.4f} - "
                    f"`{h['chunk_id']}` - {h['article_id']} / {h['product_area']} - "
                    f"{h['char_len']} chars{flag_text}**",
                    "",
                    "```",
                    h["text"],
                    "```",
                    "",
                ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    settings = get_settings()
    out = Path(settings.results_dir)
    report = run()

    write_hit_matrix(report, out / "hit_matrix.md")
    write_search_dump(report, out / "search_dump.md")
    (out / "search_eval.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    n = report["n_questions"]
    print()
    print(f"Search-only evaluation, k={report['k']}, same {n} questions, both strategies.")
    print(f"Embedding model held constant: {report['embedding_model']}")
    print()
    print(f"{'Q':<5}{'type':<12}{'article':<10}{'baseline':<12}{'structured':<12}")
    print("-" * 51)
    for q in QUESTIONS:
        b = _record(report["records"], q["id"], "baseline")
        s = _record(report["records"], q["id"], "structured")
        bv = f"HIT@{b['hit_rank']}" if b["hit"] else "MISS"
        sv = f"HIT@{s['hit_rank']}" if s["hit"] else "MISS"
        print(f"{q['id']:<5}{q['type']:<12}{q['expected_article_id']:<10}{bv:<12}{sv:<12}")
    print("-" * 51)
    print(
        f"{'':<27}{report['totals']['baseline']}/{n}"
        f"{'':<9}{report['totals']['structured']}/{n}"
    )
    print()
    sec = report["secondary"]
    print(f"{'metric':<34}{'baseline':<12}{'structured':<12}")
    print("-" * 58)
    for label, key in (
        ("hit-in-top-5", "hit_at_5"),
        ("hit-in-top-1", "hit_at_1"),
        ("mean reciprocal rank", "mrr"),
        ("chunks delivered into context", "chunks_delivered"),
        ("header-less table chunks served", "context_orphan_chunks"),
    ):
        print(f"{label:<34}{str(sec['baseline'][key]):<12}{str(sec['structured'][key]):<12}")
    print()
    print(f"Wrote {out / 'hit_matrix.md'}")
    print(f"Wrote {out / 'search_dump.md'}")
    print(f"Wrote {out / 'search_eval.json'}")


if __name__ == "__main__":
    main()
