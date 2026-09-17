"""Central configuration for the help-centre RAG evaluation app.

Everything that could change a measurement lives here, in one place, so a run is
reproducible and so the write-up can state exactly what was held constant.

The golden rule for this project: between the two chunking runs, ONLY the chunker
changes. The embedding model, the top-k, the distance metric and the corpus are
identical for both. Changing two things at once teaches you nothing.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent

# The two chunking strategies under test.
STRATEGY_BASELINE = "baseline"
STRATEGY_STRUCTURED = "structured"
STRATEGIES = (STRATEGY_BASELINE, STRATEGY_STRUCTURED)

# Retrieval modes under test in Week 4.
MODE_DENSE = "dense"
MODE_HYBRID = "hybrid"
MODES = (MODE_DENSE, MODE_HYBRID)

# One Chroma collection per strategy, so both indexes are queryable at once.
COLLECTIONS = {
    STRATEGY_BASELINE: "hc_baseline",
    STRATEGY_STRUCTURED: "hc_structured",
}


class Settings(BaseSettings):
    """Runtime settings, loaded from the environment or a local .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ----- LLM (generation only; retrieval never calls an LLM) -------------
    openrouter_api_key: str = ""
    openrouter_model: str = "google/gemini-2.5-flash"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    llm_temperature: float = 0.0
    # Answers here are two or three cited sentences. Keeping this tight cuts
    # cost and avoids provider ceilings on small credit balances.
    max_tokens: int = 320

    # ----- Embeddings ------------------------------------------------------
    # HELD CONSTANT across both chunking strategies. Do not change this in the
    # same run as a chunker change.
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # ----- Vector store ----------------------------------------------------
    chroma_dir: str = str(BASE_DIR / "chroma_db")
    corpus_dir: str = str(BASE_DIR / "corpus")
    results_dir: str = str(BASE_DIR / "results")
    # Cosine distance keeps the relevance score readable as 1 - distance.
    distance_metric: str = "cosine"

    # ----- Chunking --------------------------------------------------------
    # Same target size for both strategies. Only the boundary policy differs.
    chunk_size: int = 1000
    # Baseline overlap. The structure-aware chunker does not overlap, because it
    # packs whole structural units and never cuts one.
    chunk_overlap: int = 150

    # ----- Generation prompt ----------------------------------------------
    # Which grounding prompt to use. "v1" is the Week 3 to Week 5 prompt and is
    # what the Week 6 baseline was measured on. "v2" is the single Week 6
    # change: it separates "the facts are missing" from "the question is worded
    # in a shape the corpus does not use", and allows a refusal only for the
    # first.
    #
    # Switching this changes prompt_sha, which is the one difference
    # run_evals --compare permits between a before run and an after run.
    prompt_version: str = "v1"

    # ----- Retrieval -------------------------------------------------------
    top_k: int = 5
    # Week 4 metric. hit-rate is reported at this depth.
    eval_k: int = 3
    # Retrieval mode. "dense" is the Week 3 behaviour. "hybrid" fuses a BM25
    # arm into it, and is the single change Week 4 measures.
    retrieval_mode: str = "hybrid"
    # Reciprocal Rank Fusion constant. 60 is the conventional value and is left
    # alone on purpose, so the hybrid arm brings no tuned parameters with it.
    rrf_k: int = 60
    # BM25 parameters, at their standard defaults for the same reason.
    bm25_k1: float = 1.5
    bm25_b: float = 0.75
    # Used by the generation gate only. Search-only evaluation is never
    # threshold-filtered, so a miss is a real retrieval miss and not a
    # threshold artefact.
    score_threshold: float = 0.30

    def ensure_dirs(self) -> None:
        Path(self.chroma_dir).mkdir(parents=True, exist_ok=True)
        Path(self.results_dir).mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.ensure_dirs()
    return settings
