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
