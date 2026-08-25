"""Acceptance tests. Checks every claim the write-up makes.

    python test_acceptance.py                    retrieval only, no API key
    python test_acceptance.py --with-generation  also test citations and refusals

Exits non-zero if anything fails, so it works in CI.

These are assertions about behaviour, not a unit-test suite. Each one maps to a
sentence in results/results.md that a grader could challenge.
"""
from __future__ import annotations

import argparse
import sys

from config import STRATEGIES, STRATEGY_STRUCTURED, get_settings
from rag import term

REQUIRED_METADATA = ("source_file", "article_id", "product_area", "last_updated", "chunk_id")

passed = 0
failed = 0


def check(label: str, ok: bool, detail: str = "") -> bool:
    """Record one result and print it."""
    global passed, failed
    if ok:
        passed += 1
        print(f"{term.green('PASS')}  {label}" + (f"  {term.grey(detail)}" if detail else ""))
    else:
        failed += 1
        print(f"{term.paint('FAIL', 'red', 'bold')}  {label}" + (f"  {term.red(detail)}" if detail else ""))
    return ok


def info(label: str, detail: str) -> None:
    print(f"{term.cyan('INFO')}  {label}  {term.grey(detail)}")


# ---------------------------------------------------------------------------
def test_corpus() -> None:
    from rag.documents import load_corpus

    articles = load_corpus()
    check("corpus loads", len(articles) == 6, f"{len(articles)} articles")

    missing = [
        a.source_file
        for a in articles
        if not all([a.article_id, a.title, a.product_area, a.last_updated])
    ]
    check("every article has full front matter", not missing, str(missing))

    ids = sorted(a.article_id for a in articles)
    check("article ids are unique", len(set(ids)) == len(ids), ", ".join(ids))


def test_index() -> None:
    from rag.vector_store import count_chunks

    counts = {s: count_chunks(s) for s in STRATEGIES}
    check(
        "both indexes are built",
        all(counts.values()),
        ", ".join(f"{s}={n}" for s, n in counts.items()),
    )
    if not all(counts.values()):
        print(term.red("\n  Index is empty. Run:  python -m rag.ingest\n"))
        raise SystemExit(1)


def test_metadata() -> None:
    from rag.vector_store import get_store

    for strategy in STRATEGIES:
        got = get_store(strategy)._collection.get(include=["metadatas"])
        bad = [
            cid
            for cid, md in zip(got["ids"], got["metadatas"])
            if any(not md.get(f) for f in REQUIRED_METADATA)
        ]
        check(f"{strategy}: every chunk has full metadata", not bad, f"{len(bad)} bad")

        mismatched = [
            cid for cid, md in zip(got["ids"], got["metadatas"]) if md.get("chunk_id") != cid
        ]
        check(f"{strategy}: chunk_id matches the primary key", not mismatched)


def test_structure_guarantee() -> None:
    """The one hard promise: a table row never loses its header row."""
    from rag.vector_store import get_store

    orphans = {}
    for strategy in STRATEGIES:
        got = get_store(strategy)._collection.get(include=["metadatas"])
        orphans[strategy] = [
            cid for cid, md in zip(got["ids"], got["metadatas"]) if md.get("orphan_table_rows")
        ]

    check(
        "structure-aware: NO chunk has table rows without a header",
        not orphans[STRATEGY_STRUCTURED],
        f"{len(orphans[STRATEGY_STRUCTURED])} orphans",
    )
    info(
        "baseline, for contrast",
        f"{len(orphans['baseline'])} header-less chunks: {', '.join(orphans['baseline'])}",
    )


def test_resolvable_citations() -> None:
    from rag.vector_store import get_chunk_by_id, get_store

    for strategy in STRATEGIES:
        ids = get_store(strategy)._collection.get(include=[])["ids"]
        unresolved = [cid for cid in ids if get_chunk_by_id(strategy, cid) is None]
        check(
            f"{strategy}: every chunk_id resolves back out of the store",
            not unresolved,
            f"{len(ids)} ids checked",
        )

    check(
        "a made-up chunk_id does NOT resolve",
        get_chunk_by_id(STRATEGY_STRUCTURED, "HC-9999-structured-999") is None,
    )


def test_hit_rate() -> None:
    from evals.questions import QUESTIONS
    from evals.run_search_eval import evaluate_question

    k = get_settings().top_k
    for strategy in STRATEGIES:
        results = [evaluate_question(q, strategy, k) for q in QUESTIONS]
        hits = sum(1 for r in results if r["hit"])
        misses = [r["question_id"] for r in results if not r["hit"]]
        check(
            f"{strategy}: all 8 known-answer questions hit in top-{k}",
            hits == len(QUESTIONS),
            f"{hits}/{len(QUESTIONS)}" + (f", missed {misses}" if misses else ""),
        )


def test_metadata_filter() -> None:
    from evals.questions import FILTER_DEMO
    from rag.retriever import format_hits, search

    query, value = FILTER_DEMO["query"], FILTER_DEMO["filter_value"]
    unfiltered = format_hits(search(query, STRATEGY_STRUCTURED))
    filtered = format_hits(search(query, STRATEGY_STRUCTURED, product_area=value))

    check("filtered search returns results", bool(filtered), f"{len(filtered)} hits")
    check(
        f"every filtered result is product_area={value}",
        all(h["product_area"] == value for h in filtered),
    )
    check(
        "the filter changes top-1",
        unfiltered[0]["chunk_id"] != filtered[0]["chunk_id"],
        f"{unfiltered[0]['chunk_id']} -> {filtered[0]['chunk_id']}",
    )
    promoted = {h["chunk_id"] for h in filtered} - {h["chunk_id"] for h in unfiltered}
    check(
        "it is a pre-filter, not a post-filter",
        bool(promoted),
        f"{len(promoted)} chunk(s) promoted from outside the unfiltered top-5",
    )


def test_generation() -> None:
    """Needs an API key. Costs 6 LLM calls."""
    from evals.questions import ANSWERABLE, OUT_OF_CORPUS, get_question
    from rag.answerer import answer_question

    for qid in ANSWERABLE:
        q = get_question(qid)
        ans = answer_question(q["question"], STRATEGY_STRUCTURED, use_gate=True)
        check(f"{qid}: answered, not refused", not ans.refused)
        check(f"{qid}: produced at least one citation", bool(ans.citations))
        check(
            f"{qid}: every citation resolves",
            ans.all_citations_resolve,
            ", ".join(c.chunk_id for c in ans.citations),
        )
        check(
            f"{qid}: cited chunk really contains the answer",
            any(
                c.text and all(m.lower() in c.text.lower() for m in q["must_contain"])
                for c in ans.citations
            ),
            "must_contain: " + ", ".join(q["must_contain"]),
        )

    for item in OUT_OF_CORPUS:
        ans = answer_question(item["question"], STRATEGY_STRUCTURED, use_gate=False)
        best = ans.retrieved[0]["score"] if ans.retrieved else 0.0
        check(
            f"{item['id']}: refused an out-of-corpus question",
            ans.refused,
            f"top score {best:.4f}, gate_fired={ans.gate_fired}",
        )
        check(
            f"{item['id']}: the MODEL refused, not the gate",
            ans.refused and not ans.gate_fired,
        )



# ---------------------------------------------------------------------------
# Week 4
# ---------------------------------------------------------------------------
def test_keyword_arm() -> None:
    """The BM25 arm must keep a code as one token, or it cannot help."""
    from rag.keyword import build_index, search_keyword, tokenize
    from rag.vector_store import get_chunk_by_id, get_store

    tokens = tokenize("What does ERR-7208 mean?")
    check(
        "tokeniser keeps err-7208 as one token",
        "err-7208" in tokens,
        str(tokens),
    )
    check(
        "tokeniser also emits the parts",
        "err" in tokens and "7208" in tokens,
    )

    index = build_index(STRATEGY_STRUCTURED)
    check(
        "BM25 index covers every chunk",
        len(index) == len(get_store(STRATEGY_STRUCTURED)._collection.get(include=[])["ids"]),
        f"{len(index)} chunks",
    )
    check(
        "a rare code has a higher IDF than a common word",
        index.idf.get("err-7208", 0) > index.idf.get("the", 99),
        f"err-7208={index.idf.get('err-7208', 0):.3f} the={index.idf.get('the', 0):.3f}",
    )

    top = search_keyword("ERR-7208", STRATEGY_STRUCTURED, k=1)
    ok = bool(top) and "ERR-7208" in (get_chunk_by_id(STRATEGY_STRUCTURED, top[0][0]) or {}).get("text", "")
    check(
        "BM25 alone ranks the ERR-7208 chunk first",
        ok,
        top[0][0] if top else "nothing returned",
    )


def test_one_change_only() -> None:
    """Hybrid must differ from dense in retrieval only, nothing else."""
    from config import get_settings
    from rag.hybrid import search_hybrid
    from rag.retriever import search as search_dense

    settings = get_settings()
    check(
        "both modes share one embedding model",
        settings.embedding_model == "BAAI/bge-small-en-v1.5",
        settings.embedding_model,
    )
    check(
        "RRF constant left at the conventional value",
        settings.rrf_k == 60,
        f"rrf_k={settings.rrf_k}",
    )
    check(
        "BM25 parameters left at standard defaults",
        (settings.bm25_k1, settings.bm25_b) == (1.5, 0.75),
        f"k1={settings.bm25_k1} b={settings.bm25_b}",
    )

    q = "A customer sees ERR-4032 on their invoice. What is the cause and the fix?"
    dense_ids = {d.metadata["chunk_id"] for d, _ in search_dense(q, STRATEGY_STRUCTURED, k=20)}
    hybrid_ids = {d.metadata["chunk_id"] for d, _ in search_hybrid(q, STRATEGY_STRUCTURED, k=5)}
    check(
        "hybrid draws from the same chunk universe, it does not re-chunk",
        hybrid_ids <= dense_ids | set(build_index_ids()),
        f"{len(hybrid_ids)} fused ids",
    )


def build_index_ids() -> list:
    from rag.keyword import build_index

    return build_index(STRATEGY_STRUCTURED).ids


def test_hybrid_improves_hit_rate() -> None:
    """The headline claim: hybrid beats dense at k=3, and breaks nothing."""
    from evals.w4_measure import evaluate
    from evals.w4_questions import W4_K, W4_QUESTIONS

    before, after, regressions = 0, 0, []
    for q in W4_QUESTIONS:
        d = evaluate(q, "dense", STRATEGY_STRUCTURED)
        h = evaluate(q, "hybrid", STRATEGY_STRUCTURED)
        before += int(d["hit_at_k"])
        after += int(h["hit_at_k"])
        if d["hit_at_k"] and not h["hit_at_k"]:
            regressions.append(q["id"])

    n = len(W4_QUESTIONS)
    check(
        f"hybrid hit-rate@{W4_K} is at least dense",
        after >= before,
        f"{before}/{n} -> {after}/{n}",
    )
    check(
        f"hybrid strictly improves hit-rate@{W4_K}",
        after > before,
        f"+{after - before}",
    )
    check(
        "hybrid breaks nothing dense already found",
        not regressions,
        f"regressions: {regressions}" if regressions else "none",
    )


def test_w4_question_set() -> None:
    """The Week 4 set must be answerable from the corpus, and unrigged."""
    import pathlib

    from evals.w4_questions import W4_QUESTIONS

    corpus = " ".join(
        p.read_text(encoding="utf-8") for p in pathlib.Path("corpus").glob("*.md")
    ).lower()
    missing = [
        (q["id"], m)
        for q in W4_QUESTIONS
        for m in q["must_contain"]
        if m.lower() not in corpus
    ]
    check("every W4 answer string is verbatim in the corpus", not missing, str(missing[:3]))
    check(
        "one question per code, no duplicates",
        len({q["code"] for q in W4_QUESTIONS}) == len(W4_QUESTIONS),
        f"{len(W4_QUESTIONS)} questions",
    )


# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(description="Acceptance tests.")
    parser.add_argument(
        "--with-generation",
        action="store_true",
        help="Also test citations and refusals. Needs an API key, 6 LLM calls.",
    )
    args = parser.parse_args()
    term.init()

    print(term.grey("Loading the embedding model...\n"))

    groups = [
        ("corpus", test_corpus),
        ("index", test_index),
        ("chunk metadata", test_metadata),
        ("structure-aware guarantee", test_structure_guarantee),
        ("citation resolution", test_resolvable_citations),
        ("hit-in-top-5", test_hit_rate),
        ("product_area filter", test_metadata_filter),
        ("w4 question set", test_w4_question_set),
        ("w4 keyword arm", test_keyword_arm),
        ("w4 one change only", test_one_change_only),
        ("w4 hit-rate@3 before/after", test_hybrid_improves_hit_rate),
    ]
    if args.with_generation:
        groups.append(("generation and refusal", test_generation))

    for name, fn in groups:
        print(term.bold(f"\n-- {name}"))
        try:
            fn()
        except SystemExit:
            raise
        except Exception as exc:
            check(f"{name} raised {type(exc).__name__}", False, str(exc))

    total = passed + failed
    print()
    if failed:
        print(term.paint(f"{failed} of {total} checks FAILED", "red", "bold"))
        sys.exit(1)
    print(term.paint(f"All {total} checks passed.", "green", "bold"))
    if not args.with_generation:
        print(term.grey("Generation not tested. Add --with-generation to include it."))


if __name__ == "__main__":
    main()
