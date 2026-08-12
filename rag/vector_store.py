"""Chroma vector stores, one collection per chunking strategy.

Both collections live in the same persist directory and share one embedding
model. Keeping them side by side is what lets the evaluation run the same 8
questions against both strategies in a single process, with no re-indexing
between runs.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from langchain_chroma import Chroma

from config import COLLECTIONS, get_settings
from rag.embeddings import get_embeddings

logger = logging.getLogger(__name__)


def _collection_name(strategy: str) -> str:
    try:
        return COLLECTIONS[strategy]
    except KeyError:
        raise ValueError(
            f"Unknown strategy {strategy!r}. Expected one of {list(COLLECTIONS)}."
        ) from None


@lru_cache
def get_store(strategy: str) -> Chroma:
    """Return the cached Chroma store for one chunking strategy."""
    settings = get_settings()
    settings.ensure_dirs()
    return Chroma(
        collection_name=_collection_name(strategy),
        embedding_function=get_embeddings(),
        persist_directory=settings.chroma_dir,
        # Cosine keeps the relevance score readable as 1 - distance, so the
        # numbers pasted into results.md mean something.
        collection_metadata={"hnsw:space": settings.distance_metric},
    )


def count_chunks(strategy: str) -> int:
    try:
        return get_store(strategy)._collection.count()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Could not count %s: %s", strategy, exc)
        return 0


def reset_store(strategy: str) -> Chroma:
    """Drop and recreate one strategy's collection.

    Scoped to a single strategy on purpose. Nothing here touches any other
    collection, and nothing here re-indexes a historical corpus.
    """
    store = get_store(strategy)
    try:
        store.delete_collection()
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("delete_collection(%s) failed, continuing: %s", strategy, exc)
    get_store.cache_clear()
    return get_store(strategy)


def get_chunk_by_id(strategy: str, chunk_id: str) -> dict | None:
    """Resolve a chunk_id back to its text and metadata.

    This is what makes a citation checkable. If a citation does not resolve
    here, it is a fabricated citation.
    """
    store = get_store(strategy)
    try:
        got = store._collection.get(ids=[chunk_id], include=["documents", "metadatas"])
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("get(%s) failed: %s", chunk_id, exc)
        return None
    if not got or not got.get("ids"):
        return None
    return {
        "chunk_id": got["ids"][0],
        "text": got["documents"][0],
        "metadata": got["metadatas"][0],
    }
