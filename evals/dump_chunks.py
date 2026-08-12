"""Make every chunk_id resolvable, two ways.

1. As a file: results/chunks_<strategy>.md lists every stored chunk with an HTML
   anchor equal to its chunk_id. A citation written as
   [`HC-4002-structured-004`](chunks_structured.md#hc-4002-structured-004)
   is therefore clickable on GitHub and lands on the exact chunk.

2. From the command line, straight out of the live vector store:
       python -m evals.dump_chunks --resolve HC-4002-structured-004

Run:  python -m evals.dump_chunks
"""
from __future__ import annotations

import argparse
from pathlib import Path

from config import STRATEGIES, get_settings
from rag.vector_store import get_chunk_by_id, get_store


def all_chunks(strategy: str) -> list[dict]:
    """Read every chunk back out of the collection, in chunk_id order."""
    got = get_store(strategy)._collection.get(include=["documents", "metadatas"])
    rows = [
        {"chunk_id": cid, "text": doc, "metadata": md}
        for cid, doc, md in zip(got["ids"], got["documents"], got["metadatas"])
    ]
    return sorted(rows, key=lambda r: r["chunk_id"])


def write_chunk_file(strategy: str, path: Path) -> int:
    rows = all_chunks(strategy)
    lines = [
        f"# Every chunk in the `{strategy}` index",
        "",
        f"{len(rows)} chunks, read back from the live vector store. Each heading",
        "carries an anchor equal to its chunk_id, so citations elsewhere in the",
        "write-up link straight to the chunk they claim to come from.",
        "",
    ]
    for r in rows:
        md = r["metadata"]
        lines += [
            f"<a id=\"{r['chunk_id'].lower()}\"></a>",
            f"## `{r['chunk_id']}`",
            "",
            f"- source_file: `{md.get('source_file')}`",
            f"- article_id: `{md.get('article_id')}`",
            f"- product_area: `{md.get('product_area')}`",
            f"- last_updated: `{md.get('last_updated')}`",
            f"- chars: {md.get('char_len')}, table rows: {md.get('table_row_count')}, "
            f"header kept: {md.get('has_table_header')}, "
            f"orphan rows: {md.get('orphan_table_rows')}",
            "",
            "```",
            r["text"],
            "```",
            "",
        ]
    path.write_text("\n".join(lines), encoding="utf-8")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Dump or resolve chunks.")
    parser.add_argument("--resolve", help="Print one chunk_id and exit.")
    parser.add_argument("--strategy", default=None, help="Which index to resolve against.")
    args = parser.parse_args()

    if args.resolve:
        targets = [args.strategy] if args.strategy else list(STRATEGIES)
        for strategy in targets:
            record = get_chunk_by_id(strategy, args.resolve)
            if record:
                md = record["metadata"]
                print(f"--- {args.resolve} found in '{strategy}' ---")
                print(
                    f"source_file={md.get('source_file')}  article_id={md.get('article_id')}  "
                    f"product_area={md.get('product_area')}  last_updated={md.get('last_updated')}"
                )
                print()
                print(record["text"])
                return
        print(f"{args.resolve}: DOES NOT RESOLVE in {targets}")
        raise SystemExit(1)

    out = Path(get_settings().results_dir)
    for strategy in STRATEGIES:
        n = write_chunk_file(strategy, out / f"chunks_{strategy}.md")
        print(f"Wrote {out / f'chunks_{strategy}.md'} ({n} chunks)")


if __name__ == "__main__":
    main()
