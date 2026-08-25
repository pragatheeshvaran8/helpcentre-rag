"""Search-only retrieval, with an optional metadata filter.

Two things matter here.

1. Search-only evaluation is NEVER threshold-filtered. If a question misses, it
   misses because the chunker put the answer somewhere retrieval could not
   reach, not because a threshold quietly dropped it. Thresholding is applied
   only at generation time, and it is applied explicitly.

2. The product_area filter is a real pre-filter inside Chroma, not a post-filter
   applied to the top-5. That distinction matters: a post-filter can only remove
   results, so it can never promote a chunk that was ranked 11th into top-1. A
   pre-filter can, and requirement 4 asks us to show exactly that.
"""
from __future__ import annotations

import logging
from typing import Optional

from langchain_core.documents import Document

from config import get_settings
from rag.vector_store import get_store

logger = logging.getLogger(__name__)

ScoredDoc = tuple[Document, float]


def search(
    query: str,
    strategy: str,
    *,
    k: Optional[int] = None,
    product_area: Optional[str] = None,
) -> list[ScoredDoc]:
    """Return the top-k chunks for ``query`` from one strategy's collection.

    Args:
        query: The user question, used verbatim.
        strategy: "baseline" or "structured".
        k: How many results. Defaults to settings.top_k (5).
        product_area: When given, Chroma searches only chunks whose
            product_area metadata equals this value.
    """
    settings = get_settings()
    k = k or settings.top_k
    store = get_store(strategy)

    kwargs: dict = {}
    if product_area:
        kwargs["filter"] = {"product_area": {"$eq": product_area}}

    try:
        return store.similarity_search_with_relevance_scores(query, k=k, **kwargs)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("Search failed (%s, filter=%s): %s", strategy, product_area, exc)
        return []


def format_hits(scored: list[ScoredDoc]) -> list[dict]:
    """Flatten results into plain dicts for dumping into the write-up."""
    out: list[dict] = []
    for rank, (doc, score) in enumerate(scored, start=1):
        md = doc.metadata
        out.append(
            {
                "rank": rank,
                "score": round(float(score), 4),
                "chunk_id": md.get("chunk_id", "?"),
                "article_id": md.get("article_id", "?"),
                "source_file": md.get("source_file", "?"),
                "product_area": md.get("product_area", "?"),
                "last_updated": md.get("last_updated", "?"),
                "has_table_header": bool(md.get("has_table_header")),
                "orphan_table_rows": bool(md.get("orphan_table_rows")),
                "char_len": md.get("char_len", len(doc.page_content)),
                "text": doc.page_content,
            }
        )
        # Hybrid retrieval stashes per-arm diagnostics in metadata. Carry them
        # through when present, so the write-up can say which arm found what.
        for key in (
            "found_by",
            "dense_rank",
            "keyword_rank",
            "dense_score",
            "keyword_score",
        ):
            if key in md:
                out[-1][key] = md[key]
    return out


def chunk_answers_question(text: str, must_contain: list[str]) -> bool:
    """Does this chunk literally contain every required piece of the answer?

    Case-insensitive substring match. This is the objective half of the hit
    rule. It is deliberately unforgiving: a chunk that mentions the error code
    but has lost the fix cannot answer the question, so it is not a hit.
    """
    haystack = text.lower()
    return all(needle.lower() in haystack for needle in must_contain)


def format_context(scored: list[ScoredDoc]) -> str:
    """Render retrieved chunks as labelled context blocks for the prompt.

    Every block is labelled with its chunk_id, because the generation prompt
    requires the model to cite that exact id. A model cannot cite an id it was
    never shown.
    """
    if not scored:
        return "NO CONTEXT BLOCKS WERE RETRIEVED."
    blocks: list[str] = []
    for doc, score in scored:
        md = doc.metadata
        blocks.append(
            f"[{md.get('chunk_id', '?')}] "
            f"(article {md.get('article_id', '?')}, "
            f"file {md.get('source_file', '?')}, "
            f"area {md.get('product_area', '?')}, "
            f"updated {md.get('last_updated', '?')}, "
            f"score {float(score):.4f})\n{doc.page_content.strip()}"
        )
    return "\n\n---\n\n".join(blocks)
