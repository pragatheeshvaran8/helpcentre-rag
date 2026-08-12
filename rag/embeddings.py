"""Embedding model factory.

Deliberately boring. One model, loaded once, used by BOTH chunking strategies.

There is no provider switch here on purpose. The most common way to ruin this
measurement is to change the chunker and the embedding model in the same run and
then report a single number. With one model hard-wired, any difference between
the two runs can only come from chunking.
"""
from __future__ import annotations

import logging
from functools import lru_cache

from langchain_core.embeddings import Embeddings
from langchain_huggingface import HuggingFaceEmbeddings

from config import get_settings

logger = logging.getLogger(__name__)


@lru_cache
def get_embeddings() -> Embeddings:
    """Return the cached local embedding model."""
    settings = get_settings()
    logger.info("Loading embedding model: %s", settings.embedding_model)
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        # Normalised vectors keep cosine distance well behaved, which is what
        # the reported relevance scores are built on.
        encode_kwargs={"normalize_embeddings": True},
    )


def embedding_backend_name() -> str:
    return f"local:{get_settings().embedding_model}"
