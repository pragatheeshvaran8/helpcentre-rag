"""Hybrid retrieval: the dense arm fused with the BM25 arm using RRF.

THIS IS THE ONE CHANGE
    Week 4 allows exactly one change, so this is it. Everything else is frozen:
    the same 6 articles, the same structure-aware chunker, the same embedding
    model, the same Chroma collections, the same k. The only difference between
    the before-number and the after-number is whether the BM25 arm is fused in.

    Because it is one flag, the comparison is auditable. Nobody has to take my
    word for what changed.

WHY RECIPROCAL RANK FUSION
    The two arms produce scores on incompatible scales. Cosine relevance sits
    around 0.6 to 0.9. BM25 is unbounded and depends on IDF. Adding or averaging
    them needs a normaliser, and every normaliser needs tuning, which would be a
    second change smuggled in.

    RRF ignores the scores entirely and uses only the ranks:

        rrf(d) = sum over arms of  1 / (rrf_k + rank(d))

    So it has one constant, and the conventional value of 60 is used unchanged.
    A document ranked first by either arm gets a strong contribution. A document
    both arms like ranks highest of all.

WHAT THIS SHOULD FIX, AND WHAT IT SHOULD NOT
    It should fix questions that name a rare exact token, because BM25 ranks the
    chunk holding `ERR-7208` first while the dense arm cannot see it.

    It should NOT fix a question whose answer was chunked away, or one where the
    right chunk was retrieved and the model still answered badly. Those are the
    other failure bucket, and the write-up reports what the change did not fix.
"""
from __future__ import annotations

import logging
from typing import Optional

from langchain_core.documents import Document

from config import get_settings
from rag.keyword import build_index, search_keyword
from rag.retriever import ScoredDoc, search as search_dense

logger = logging.getLogger(__name__)

# How many candidates each arm contributes before fusion. Deeper than the final
# k on purpose: a chunk ranked 8th by one arm can still win after fusion, and
# that headroom is where hybrid earns its keep.
CANDIDATE_DEPTH = 20


def search_hybrid(
    query: str,
    strategy: str,
    *,
    k: Optional[int] = None,
    product_area: Optional[str] = None,
    depth: int = CANDIDATE_DEPTH,
) -> list[ScoredDoc]:
    """Fuse dense and BM25 rankings with RRF and return the top-k.

    The returned objects match ``search()``: a list of (Document, score) pairs,
    so this drops straight into the existing answerer and formatters. The score
    is the RRF score, not a similarity, so it is small by nature. The component
    ranks and the dense score are copied into metadata for the write-up.
    """
    settings = get_settings()
    k = k or settings.top_k
    rrf_k = settings.rrf_k

    dense_hits = search_dense(query, strategy, k=depth, product_area=product_area)
    keyword_hits = search_keyword(query, strategy, k=depth, product_area=product_area)

    dense_rank: dict[str, int] = {}
    dense_score: dict[str, float] = {}
    dense_doc: dict[str, Document] = {}
    for rank, (doc, score) in enumerate(dense_hits, start=1):
        chunk_id = doc.metadata.get("chunk_id")
        if chunk_id and chunk_id not in dense_rank:
            dense_rank[chunk_id] = rank
            dense_score[chunk_id] = float(score)
            dense_doc[chunk_id] = doc

    keyword_rank: dict[str, int] = {}
    keyword_score: dict[str, float] = {}
    for rank, (chunk_id, score) in enumerate(keyword_hits, start=1):
        if chunk_id not in keyword_rank:
            keyword_rank[chunk_id] = rank
            keyword_score[chunk_id] = float(score)

    fused: dict[str, float] = {}
    for chunk_id, rank in dense_rank.items():
        fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (rrf_k + rank)
    for chunk_id, rank in keyword_rank.items():
        fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (rrf_k + rank)

    # Ties broken by chunk_id so a rerun is deterministic.
    order = sorted(fused.items(), key=lambda pair: (-pair[1], pair[0]))[:k]

    index = build_index(strategy)
    results: list[ScoredDoc] = []
    for chunk_id, rrf_score in order:
        doc = dense_doc.get(chunk_id)
        if doc is None:
            # BM25 found it and the dense arm did not, so build the Document
            # from the BM25 index. This is the interesting case.
            try:
                i = index.ids.index(chunk_id)
            except ValueError:  # pragma: no cover - defensive
                logger.warning("Fused id %s is in neither arm", chunk_id)
                continue
            doc = Document(page_content=index.texts[i], metadata=dict(index.metadatas[i]))
        else:
            doc = Document(page_content=doc.page_content, metadata=dict(doc.metadata))

        doc.metadata["dense_rank"] = dense_rank.get(chunk_id, 0)
        doc.metadata["keyword_rank"] = keyword_rank.get(chunk_id, 0)
        doc.metadata["dense_score"] = round(dense_score.get(chunk_id, 0.0), 4)
        doc.metadata["keyword_score"] = round(keyword_score.get(chunk_id, 0.0), 4)
        doc.metadata["found_by"] = _found_by(chunk_id, dense_rank, keyword_rank)
        results.append((doc, rrf_score))

    return results


def _found_by(chunk_id: str, dense_rank: dict, keyword_rank: dict) -> str:
    in_dense = chunk_id in dense_rank
    in_keyword = chunk_id in keyword_rank
    if in_dense and in_keyword:
        return "both"
    if in_keyword:
        return "keyword only"
    return "dense only"


def search_by_mode(
    query: str,
    strategy: str,
    *,
    mode: str,
    k: Optional[int] = None,
    product_area: Optional[str] = None,
) -> list[ScoredDoc]:
    """Dispatch to one retrieval mode.

    ``mode`` is "dense" for the Week 3 behaviour, or "hybrid" for the one
    change. Keeping both behind a single argument is what makes the
    before-and-after a single flag rather than a code edit.
    """
    if mode == "dense":
        return search_dense(query, strategy, k=k, product_area=product_area)
    if mode == "hybrid":
        return search_hybrid(query, strategy, k=k, product_area=product_area)
    raise ValueError(f"Unknown retrieval mode {mode!r}. Expected 'dense' or 'hybrid'.")
