"""Ingest the 6 new help-centre articles under both chunking strategies.

TIME REALITY (task requirement 6)
    This script indexes the 6 NEW articles only. There is no historical corpus
    in this index and nothing else is re-indexed. Each strategy's collection is
    dropped and rebuilt from those 6 files, which takes seconds, not minutes.

METADATA (task requirement 1)
    Every chunk carries source_file, article_id, product_area and last_updated,
    inherited from the article front matter, plus a stable chunk_id used as the
    Chroma primary key so citations can be resolved later. Ingest refuses to
    store a chunk that is missing any of them.

Run:  python -m rag.ingest
"""
from __future__ import annotations

import argparse
import logging

from langchain_core.documents import Document

from config import STRATEGIES, get_settings
from rag import term
from rag.chunkers import CHUNKERS, table_stats
from rag.documents import Article, load_corpus
from rag.vector_store import count_chunks, get_store, reset_store

logger = logging.getLogger(__name__)

REQUIRED_CHUNK_METADATA = ("source_file", "article_id", "product_area", "last_updated")


def make_chunk_id(article_id: str, strategy: str, index: int) -> str:
    """Stable, human-readable, resolvable chunk id: HC-4002-structured-007."""
    return f"{article_id}-{strategy}-{index:03d}"


def build_documents(article: Article, strategy: str) -> list[Document]:
    """Chunk one article under one strategy and attach full metadata."""
    texts = CHUNKERS[strategy](article.body)
    docs: list[Document] = []
    for i, text in enumerate(texts, start=1):
        chunk_id = make_chunk_id(article.article_id, strategy, i)
        metadata = article.base_metadata() | {
            "chunk_id": chunk_id,
            "strategy": strategy,
            "chunk_index": i,
            "char_len": len(text),
            **table_stats(text),
        }
        missing = [f for f in REQUIRED_CHUNK_METADATA if not metadata.get(f)]
        if missing:
            # A chunk with no source_file is a failed ingest. Fail loudly.
            raise ValueError(f"{chunk_id}: metadata missing {missing}")
        docs.append(Document(page_content=text, metadata=metadata))
    return docs


def ingest_strategy(articles: list[Article], strategy: str) -> dict:
    """Rebuild one strategy's collection from the given articles."""
    reset_store(strategy)
    store = get_store(strategy)

    docs: list[Document] = []
    for article in articles:
        docs.extend(build_documents(article, strategy))

    store.add_documents(docs, ids=[d.metadata["chunk_id"] for d in docs])

    orphans = sum(1 for d in docs if d.metadata["orphan_table_rows"])
    with_rows = sum(1 for d in docs if d.metadata["contains_table_rows"])
    lengths = [d.metadata["char_len"] for d in docs]

    return {
        "strategy": strategy,
        "articles": len(articles),
        "chunks": len(docs),
        "stored": count_chunks(strategy),
        "chunks_with_table_rows": with_rows,
        "chunks_with_orphan_rows": orphans,
        "orphan_rate": round(orphans / with_rows, 3) if with_rows else 0.0,
        "mean_chars": round(sum(lengths) / len(lengths)) if lengths else 0,
        "max_chars": max(lengths) if lengths else 0,
    }


def ingest_all() -> list[dict]:
    """Ingest the 6 new articles under every strategy."""
    settings = get_settings()
    articles = load_corpus(settings.corpus_dir)
    logger.info("Loaded %d new articles from %s", len(articles), settings.corpus_dir)
    return [ingest_strategy(articles, s) for s in STRATEGIES]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Ingest the 6 new help-centre articles.")
    parser.parse_args()

    term.init()
    stats = ingest_all()
    print()
    print(term.green("Ingest complete. NEW ARTICLES ONLY - no historical corpus re-indexed."))
    print()
    header = (
        f"{'strategy':<12}{'articles':>9}{'chunks':>8}{'stored':>8}"
        f"{'tbl-chunks':>12}{'orphan':>8}{'orphan%':>9}{'mean':>7}{'max':>6}"
    )
    print(term.bold(header))
    print("-" * len(header))
    for s in stats:
        # Pad first, then colour. ANSI codes count toward f-string width.
        orphan = f"{s['chunks_with_orphan_rows']:>8}"
        rate = f"{s['orphan_rate'] * 100:>8.1f}%"
        if s["chunks_with_orphan_rows"]:
            orphan, rate = term.paint(orphan, "red", "bold"), term.paint(rate, "red", "bold")
        else:
            orphan, rate = term.green(orphan), term.green(rate)
        print(
            f"{s['strategy']:<12}{s['articles']:>9}{s['chunks']:>8}{s['stored']:>8}"
            f"{s['chunks_with_table_rows']:>12}{orphan}{rate}"
            f"{s['mean_chars']:>7}{s['max_chars']:>6}"
        )
    print()
    print(term.grey("orphan = chunk holds table data rows but has lost its header row."))


if __name__ == "__main__":
    main()
