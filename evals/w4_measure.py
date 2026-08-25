"""Week 4 headline number: hit-rate@3 before and after the one change.

No LLM is called in this file. It measures retrieval and nothing else, so the
number cannot be contaminated by the model knowing an answer from training.

WHAT CHANGES BETWEEN THE TWO RUNS
    Exactly one thing: the retrieval mode.

        dense   the Week 3 behaviour, vector search alone
        hybrid  the same vector search, fused with a BM25 arm by RRF

    Frozen across both: the 6 articles, the structure-aware chunker, the
    embedding model, the Chroma collection, k, and the hit rule.

WHY A DEEPER WINDOW IS ALSO RECORDED
    hit-rate@3 is pass or fail, which hides how badly a question missed. Each
    question is therefore also searched to depth 10, so a miss can be diagnosed
    as "just outside the window" or "nowhere near". That costs nothing extra and
    it is what makes the failure labelling honest.

Run:  python -m evals.w4_measure
"""
from __future__ import annotations

import json
from pathlib import Path

from config import MODES, STRATEGY_STRUCTURED, get_settings
from evals.w4_questions import W4_K, W4_QUESTIONS
from rag import term
from rag.hybrid import search_by_mode
from rag.retriever import chunk_answers_question, format_hits

# Searched depth for diagnosis. The graded metric still uses W4_K.
DIAGNOSTIC_DEPTH = 10


def evaluate(question: dict, mode: str, strategy: str) -> dict:
    """Search one question in one mode and record where the answer landed."""
    hits = format_hits(
        search_by_mode(question["question"], strategy, mode=mode, k=DIAGNOSTIC_DEPTH)
    )

    answer_rank = None
    for h in hits:
        right_article = h["article_id"] == question["expected_article_id"]
        has_answer = chunk_answers_question(h["text"], question["must_contain"])
        h["is_answer_chunk"] = right_article and has_answer
        if h["is_answer_chunk"] and answer_rank is None:
            answer_rank = h["rank"]

    top = hits[:W4_K]
    return {
        "question_id": question["id"],
        "code": question["code"],
        "mode": mode,
        # The graded metric.
        "hit_at_k": answer_rank is not None and answer_rank <= W4_K,
        # Diagnosis.
        "answer_rank": answer_rank,
        "within_depth": answer_rank is not None,
        "top1_chunk_id": hits[0]["chunk_id"] if hits else None,
        "found_by": hits[0].get("found_by") if hits else None,
        # Which arm surfaced the answering chunk, when hybrid found one.
        "answer_found_by": next(
            (h.get("found_by") for h in hits if h.get("is_answer_chunk")), None
        ),
        "answer_dense_rank": next(
            (h.get("dense_rank") for h in hits if h.get("is_answer_chunk")), None
        ),
        "answer_keyword_rank": next(
            (h.get("keyword_rank") for h in hits if h.get("is_answer_chunk")), None
        ),
        "top_k_chunk_ids": [h["chunk_id"] for h in top],
        "hits": hits,
    }


def summarise(records: list[dict], mode: str) -> dict:
    subset = [r for r in records if r["mode"] == mode]
    n = len(subset)
    ranks = [r["answer_rank"] for r in subset if r["answer_rank"]]
    return {
        "mode": mode,
        "n": n,
        "hit_at_k": sum(1 for r in subset if r["hit_at_k"]),
        "hit_at_1": sum(1 for r in subset if r["answer_rank"] == 1),
        "within_depth": sum(1 for r in subset if r["within_depth"]),
        "never_found": sum(1 for r in subset if not r["within_depth"]),
        "mrr": round(sum(1 / r for r in ranks) / n, 4) if n else 0.0,
        "misses": [r["question_id"] for r in subset if not r["hit_at_k"]],
    }


def run(strategy: str = STRATEGY_STRUCTURED) -> dict:
    settings = get_settings()
    records = [
        evaluate(q, mode, strategy) for q in W4_QUESTIONS for mode in MODES
    ]
    return {
        "k": W4_K,
        "diagnostic_depth": DIAGNOSTIC_DEPTH,
        "strategy": strategy,
        "n_questions": len(W4_QUESTIONS),
        "embedding_model": settings.embedding_model,
        "rrf_k": settings.rrf_k,
        "bm25": {"k1": settings.bm25_k1, "b": settings.bm25_b},
        "summary": {mode: summarise(records, mode) for mode in MODES},
        "records": records,
    }


def _rec(records: list[dict], qid: str, mode: str) -> dict:
    return next(r for r in records if r["question_id"] == qid and r["mode"] == mode)


def write_report(report: dict, path: Path) -> None:
    recs = report["records"]
    k = report["k"]
    before, after = report["summary"]["dense"], report["summary"]["hybrid"]
    n = report["n_questions"]
    delta = after["hit_at_k"] - before["hit_at_k"]

    lines = [
        f"# Week 4: hit-rate@{k} before and after one change",
        "",
        f"- Questions: {n}, one per code in the corpus",
        f"- Index: `{report['strategy']}` (the chunker Week 3 shipped, unchanged)",
        f"- Embedding model: `{report['embedding_model']}` (unchanged)",
        f"- The one change: retrieval mode `dense` -> `hybrid` (BM25 fused by RRF, "
        f"rrf_k={report['rrf_k']}, BM25 k1={report['bm25']['k1']}, b={report['bm25']['b']})",
        "- No LLM was called to produce this file.",
        "",
        "## The number",
        "",
        f"| | hit-rate@{k} | hit@1 | MRR | answer never in top-{report['diagnostic_depth']} |",
        "|---|---|---|---|---|",
        f"| **before** (dense) | **{before['hit_at_k']}/{n}** | {before['hit_at_1']}/{n} "
        f"| {before['mrr']} | {before['never_found']} |",
        f"| **after** (hybrid) | **{after['hit_at_k']}/{n}** | {after['hit_at_1']}/{n} "
        f"| {after['mrr']} | {after['never_found']} |",
        f"| change | **{delta:+d}** | {after['hit_at_1'] - before['hit_at_1']:+d} "
        f"| {after['mrr'] - before['mrr']:+.4f} | "
        f"{after['never_found'] - before['never_found']:+d} |",
        "",
        "## Per-question record",
        "",
        "`rank` is where the answering chunk landed, out of "
        f"{report['diagnostic_depth']} searched. `-` means it was never found.",
        "`arm` shows which retrieval arm surfaced it after fusion.",
        "",
        f"| Q | code | article | before hit@{k} | rank | after hit@{k} | rank | arm |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for q in W4_QUESTIONS:
        b = _rec(recs, q["id"], "dense")
        a = _rec(recs, q["id"], "hybrid")
        lines.append(
            f"| {q['id']} | `{q['code']}` | {q['expected_article_id']} "
            f"| {'HIT' if b['hit_at_k'] else 'MISS'} | {b['answer_rank'] or '-'} "
            f"| {'HIT' if a['hit_at_k'] else 'MISS'} | {a['answer_rank'] or '-'} "
            f"| {a['answer_found_by'] or '-'} |"
        )

    fixed = [
        q["id"]
        for q in W4_QUESTIONS
        if not _rec(recs, q["id"], "dense")["hit_at_k"]
        and _rec(recs, q["id"], "hybrid")["hit_at_k"]
    ]
    broke = [
        q["id"]
        for q in W4_QUESTIONS
        if _rec(recs, q["id"], "dense")["hit_at_k"]
        and not _rec(recs, q["id"], "hybrid")["hit_at_k"]
    ]
    still = [
        q["id"]
        for q in W4_QUESTIONS
        if not _rec(recs, q["id"], "dense")["hit_at_k"]
        and not _rec(recs, q["id"], "hybrid")["hit_at_k"]
    ]

    lines += [
        "",
        "## What the change did",
        "",
        f"- Fixed ({len(fixed)}): {', '.join(fixed) if fixed else 'none'}",
        f"- Broke ({len(broke)}): {', '.join(broke) if broke else 'none'}",
        f"- Still failing ({len(still)}): {', '.join(still) if still else 'none'}",
        "",
        "The still-failing list matters as much as the fixed list. Those are the",
        "questions this change was never going to help, and they are labelled by",
        "failure type in `w4_failures.md`.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_dump(report: dict, path: Path) -> None:
    lines = [
        f"# Week 4 search-only dump: {report['n_questions']} questions, both modes",
        "",
        f"Depth {report['diagnostic_depth']} searched, hit-rate graded at "
        f"{report['k']}. `ANSWER` marks the chunk that satisfies the hit rule.",
        "",
    ]
    for q in W4_QUESTIONS:
        lines += [
            "---",
            "",
            f"## {q['id']} - `{q['code']}`",
            "",
            f"**Question:** {q['question']}",
            "",
            f"**Known-correct location:** `{q['expected_article_id']}` -> {q['expected_section']}",
            "",
            "**Hit requires:** " + ", ".join(f"`{m}`" for m in q["must_contain"]),
            "",
        ]
        for mode in MODES:
            r = _rec(report["records"], q["id"], mode)
            verdict = (
                f"HIT at rank {r['answer_rank']}"
                if r["hit_at_k"]
                else (
                    f"MISS (answer at rank {r['answer_rank']})"
                    if r["answer_rank"]
                    else "MISS (answer never retrieved)"
                )
            )
            lines += [f"### {mode} -> {verdict}", ""]
            for h in r["hits"][: report["diagnostic_depth"]]:
                tags = []
                if h.get("is_answer_chunk"):
                    tags.append("ANSWER")
                if h.get("found_by"):
                    tags.append(h["found_by"])
                if h.get("orphan_table_rows"):
                    tags.append("ORPHAN")
                tag = ("  [" + ", ".join(tags) + "]") if tags else ""
                extra = ""
                if mode == "hybrid":
                    extra = (
                        f"  dense_rank={h.get('dense_rank')} "
                        f"kw_rank={h.get('keyword_rank')} "
                        f"dense={h.get('dense_score')} kw={h.get('keyword_score')}"
                    )
                lines.append(
                    f"- {h['rank']}. score {h['score']:.4f}  `{h['chunk_id']}`  "
                    f"{h['article_id']}{tag}{extra}"
                )
            lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    term.init()
    settings = get_settings()
    out = Path(settings.results_dir)
    report = run()

    write_report(report, out / "w4_hitrate.md")
    write_dump(report, out / "w4_search_dump.md")
    (out / "w4_measure.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    n = report["n_questions"]
    k = report["k"]
    before, after = report["summary"]["dense"], report["summary"]["hybrid"]

    print()
    print(term.bold(f"Week 4 search-only, {n} questions, hit-rate@{k}"))
    print(term.grey("one change: dense -> hybrid (BM25 fused by RRF). Nothing else moved."))
    print()
    print(term.bold(f"{'Q':<5}{'code':<11}{'before':<10}{'after':<10}{'arm':<14}"))
    print("-" * 50)
    for q in W4_QUESTIONS:
        b = _rec(report["records"], q["id"], "dense")
        a = _rec(report["records"], q["id"], "hybrid")
        bt = f"{'HIT@' + str(b['answer_rank']) if b['hit_at_k'] else 'MISS':<10}"
        at = f"{'HIT@' + str(a['answer_rank']) if a['hit_at_k'] else 'MISS':<10}"
        print(
            f"{q['id']:<5}{q['code']:<11}"
            f"{term.green(bt) if b['hit_at_k'] else term.red(bt)}"
            f"{term.green(at) if a['hit_at_k'] else term.red(at)}"
            f"{term.grey(str(a['answer_found_by'] or '-'))}"
        )
    print("-" * 50)
    delta = after["hit_at_k"] - before["hit_at_k"]
    print()
    for label, s in (("before (dense)", before), ("after (hybrid)", after)):
        print(
            f"  {label:<18} hit@{k}={s['hit_at_k']}/{n}  hit@1={s['hit_at_1']}/{n}  "
            f"MRR={s['mrr']}  never-found={s['never_found']}"
        )
    verdict = f"hit-rate@{k}: {before['hit_at_k']}/{n} -> {after['hit_at_k']}/{n}  ({delta:+d})"
    print()
    print(term.paint(verdict, "green" if delta > 0 else "yellow", "bold"))
    print()
    print(f"Wrote {out / 'w4_hitrate.md'}")
    print(f"Wrote {out / 'w4_search_dump.md'}")


if __name__ == "__main__":
    main()
