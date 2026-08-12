"""Requirement 4: show one query where a product_area filter changes top-1.

The filter is a Chroma pre-filter, applied inside the search, not a post-filter
applied to an already-returned top-5. That matters. A post-filter can only
delete rows, so it can never promote a chunk that was ranked 11th into top-1.
A pre-filter can, and that is what this run demonstrates.

The query is deliberately ambiguous. "Retries" is documented in three different
product areas: payments (the dunning schedule), subscriptions (renewal retries)
and api (webhook backoff). Unfiltered search has to guess which one the user
meant. The filter removes the guess.

Run:  python -m evals.run_filter_demo
"""
from __future__ import annotations

import json
from pathlib import Path

from config import STRATEGY_STRUCTURED, get_settings
from evals.questions import FILTER_DEMO
from rag.retriever import format_hits, search


def _table(hits: list[dict]) -> list[str]:
    rows = [
        "| rank | score | chunk_id | article | product_area | last_updated |",
        "|---|---|---|---|---|---|",
    ]
    for h in hits:
        rows.append(
            f"| {h['rank']} | {h['score']:.4f} | `{h['chunk_id']}` | {h['article_id']} "
            f"| {h['product_area']} | {h['last_updated']} |"
        )
    return rows


def _blocks(hits: list[dict]) -> list[str]:
    out: list[str] = []
    for h in hits:
        out += [
            f"**{h['rank']}. score {h['score']:.4f} - `{h['chunk_id']}` - "
            f"{h['article_id']} / {h['product_area']}**",
            "",
            "```",
            h["text"],
            "```",
            "",
        ]
    return out


def run(strategy: str = STRATEGY_STRUCTURED) -> dict:
    settings = get_settings()
    query = FILTER_DEMO["query"]
    field = FILTER_DEMO["filter_field"]
    value = FILTER_DEMO["filter_value"]

    unfiltered = format_hits(search(query, strategy, k=settings.top_k))
    filtered = format_hits(
        search(query, strategy, k=settings.top_k, product_area=value)
    )

    return {
        "query": query,
        "strategy": strategy,
        "filter": {field: value},
        "unfiltered": unfiltered,
        "filtered": filtered,
        "top1_changed": (
            bool(unfiltered)
            and bool(filtered)
            and unfiltered[0]["chunk_id"] != filtered[0]["chunk_id"]
        ),
        "unfiltered_areas": sorted({h["product_area"] for h in unfiltered}),
        "filtered_areas": sorted({h["product_area"] for h in filtered}),
    }


def write_report(result: dict, path: Path) -> None:
    u, f = result["unfiltered"], result["filtered"]
    changed = "YES" if result["top1_changed"] else "NO"
    lines = [
        "# Metadata filter on product_area",
        "",
        f"- Query: **{result['query']}**",
        f"- Strategy searched: `{result['strategy']}`",
        f"- Filter: `{json.dumps(result['filter'])}` (Chroma pre-filter, applied inside the search)",
        f"- Top-1 changed: **{changed}**",
        "",
        f"Unfiltered top-1: `{u[0]['chunk_id']}` from {u[0]['article_id']} "
        f"(product_area `{u[0]['product_area']}`), score {u[0]['score']:.4f}.",
        "",
        f"Filtered top-1: `{f[0]['chunk_id']}` from {f[0]['article_id']} "
        f"(product_area `{f[0]['product_area']}`), score {f[0]['score']:.4f}.",
        "",
        f"Product areas present unfiltered: {', '.join(result['unfiltered_areas'])}.",
        f"Product areas present filtered: {', '.join(result['filtered_areas'])}.",
        "",
        "## Result list A - UNFILTERED",
        "",
        *_table(u),
        "",
        *_blocks(u),
        "## Result list B - FILTERED to product_area = "
        f"`{result['filter']['product_area']}`",
        "",
        *_table(f),
        "",
        *_blocks(f),
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    settings = get_settings()
    out = Path(settings.results_dir)
    result = run()
    write_report(result, out / "filter_demo.md")
    (out / "filter_demo.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print()
    print(f"Query: {result['query']}")
    print(f"Filter: {result['filter']}")
    print()
    for label, hits in (("UNFILTERED", result["unfiltered"]), ("FILTERED", result["filtered"])):
        print(f"--- {label} ---")
        for h in hits:
            print(
                f"  {h['rank']}. {h['score']:.4f}  {h['chunk_id']:<26}"
                f"{h['article_id']:<10}{h['product_area']}"
            )
        print()
    print(f"top-1 changed: {result['top1_changed']}")
    print(f"Wrote {out / 'filter_demo.md'}")


if __name__ == "__main__":
    main()
