"""Grounded generation with a FORCED refusal and a citation on every claim.

The grounding prompt below never says "use your best judgement" and never says
"if the context is insufficient, do your best". Those sentences are exactly how
an invented fix for ERR-4032 reaches a customer. The refusal here is an
instruction with a fixed output string, not a suggestion.

Two independent layers stop an invented answer:

  Layer 1 - retrieval gate (optional, off for the refusal transcripts).
      If nothing clears the score threshold, refuse without calling the model.

  Layer 2 - the prompt itself.
      The model is shown the retrieved context and must refuse in a fixed form
      when that context does not contain the answer.

The refusal transcripts in results.md are produced with Layer 1 DISABLED on
purpose. That means the model really did see retrieved context and still had to
refuse. A refusal produced by a code path that never called the model would
prove nothing about the prompt.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from config import get_settings
from rag.retriever import format_context, search
from rag.vector_store import get_chunk_by_id

logger = logging.getLogger(__name__)

# The exact string the model must emit when it cannot answer.
REFUSAL_TOKEN = "REFUSED"

# chunk_id looks like HC-4002-structured-007
CITATION_RE = re.compile(r"\[((?:HC-\d{4})-(?:baseline|structured)-\d{3})\]")

SYSTEM_PROMPT = """You are a support-desk answering assistant for a help-centre corpus.

You answer ONLY from the CONTEXT BLOCKS given to you in the user message.
Each block is labelled with a chunk_id in square brackets, like [HC-4002-structured-007].

RULES. These are absolute. There is no situation in which you may break them.

1. Every single sentence of your answer MUST end with a citation naming the block
   it came from, written exactly as [chunk_id]. A sentence with no citation is a
   rule violation.
2. You may cite ONLY chunk_ids that appear in the CONTEXT BLOCKS below. Never
   invent, guess, abbreviate or reformat a chunk_id.
3. You may state ONLY facts that are written in the CONTEXT BLOCKS. You may not
   use outside knowledge. You may not infer. You may not generalise. You may not
   fill a gap with something that sounds reasonable.
4. If the CONTEXT BLOCKS do not contain the information needed to answer the
   question, you MUST reply with exactly this, and nothing else:

REFUSED: The help-centre corpus does not contain this information.
Missing: <one short line naming what was asked for and not found>

5. A partial answer is a refusal. If you can answer only part of the question,
   you must still refuse using the format in rule 4, and name the missing part.
6. Never apologise, never offer a workaround, never suggest what the answer
   might be, and never tell the user to check elsewhere.

You are measured on refusing correctly, not on being helpful."""

USER_TEMPLATE = """CONTEXT BLOCKS:

{context}

END OF CONTEXT BLOCKS.

QUESTION: {question}"""


@dataclass
class Citation:
    """One [chunk_id] the model produced, and whether it actually resolves."""

    chunk_id: str
    resolves: bool
    was_in_context: bool
    article_id: str | None = None
    source_file: str | None = None
    text: str | None = None


@dataclass
class Answer:
    """The full record of one generation, enough to paste into the write-up."""

    question: str
    strategy: str
    answer: str
    refused: bool
    gate_fired: bool
    retrieved: list[dict] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    context: str = ""

    @property
    def all_citations_resolve(self) -> bool:
        return bool(self.citations) and all(c.resolves for c in self.citations)


def _llm():
    """Build the chat model. Imported lazily so search-only runs need no key."""
    from langchain_openai import ChatOpenAI

    settings = get_settings()
    if not settings.openrouter_api_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Generation needs it; search-only "
            "evaluation does not."
        )
    return ChatOpenAI(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        temperature=settings.llm_temperature,
        max_tokens=settings.max_tokens,
        timeout=120,
    )


def verify_citations(text: str, strategy: str, context_ids: set[str]) -> list[Citation]:
    """Resolve every [chunk_id] in ``text`` against the live vector store."""
    citations: list[Citation] = []
    for chunk_id in dict.fromkeys(CITATION_RE.findall(text)):
        record = get_chunk_by_id(strategy, chunk_id)
        citations.append(
            Citation(
                chunk_id=chunk_id,
                resolves=record is not None,
                was_in_context=chunk_id in context_ids,
                article_id=(record or {}).get("metadata", {}).get("article_id"),
                source_file=(record or {}).get("metadata", {}).get("source_file"),
                text=(record or {}).get("text"),
            )
        )
    return citations


def answer_question(
    question: str,
    strategy: str,
    *,
    k: int | None = None,
    product_area: str | None = None,
    use_gate: bool = True,
) -> Answer:
    """Retrieve, then answer strictly from what was retrieved, or refuse.

    Args:
        use_gate: When True, refuse without calling the model if nothing clears
            settings.score_threshold. Set False to force the model itself to do
            the refusing, which is what the refusal transcripts demonstrate.
    """
    settings = get_settings()
    scored = search(question, strategy, k=k, product_area=product_area)
    from rag.retriever import format_hits  # local import avoids a cycle at import time

    retrieved = format_hits(scored)

    above = [(d, s) for d, s in scored if s >= settings.score_threshold]
    if use_gate and not above:
        best = max((s for _, s in scored), default=0.0)
        return Answer(
            question=question,
            strategy=strategy,
            answer=(
                f"{REFUSAL_TOKEN}: The help-centre corpus does not contain this "
                f"information.\nMissing: nothing retrieved above the "
                f"{settings.score_threshold} relevance gate (best was {best:.4f})."
            ),
            refused=True,
            gate_fired=True,
            retrieved=retrieved,
        )

    context = format_context(scored)
    context_ids = {h["chunk_id"] for h in retrieved}

    response = _llm().invoke(
        [
            ("system", SYSTEM_PROMPT),
            ("human", USER_TEMPLATE.format(context=context, question=question)),
        ]
    )
    text = (response.content or "").strip()

    return Answer(
        question=question,
        strategy=strategy,
        answer=text,
        refused=text.upper().startswith(REFUSAL_TOKEN),
        gate_fired=False,
        retrieved=retrieved,
        citations=verify_citations(text, strategy, context_ids),
        context=context,
    )
