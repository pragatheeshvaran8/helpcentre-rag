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

SYSTEM_PROMPT_V1 = """You are a support-desk answering assistant for a help-centre corpus.

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


# ---------------------------------------------------------------------------
# Version 2: the single Week 6 change.
# ---------------------------------------------------------------------------
# Week 5 read 20 traces by hand and named the top problem: the app refuses
# questions the corpus can answer. The Week 6 baseline confirmed it at scale.
# 21 of 27 failing cases carry false_refusal, and retrieval_miss is 0, so the
# answering chunk was on screen every single time.
#
# Week 5 also named the cause. The failures asked for a SHAPE the corpus does
# not have while asking for SUBSTANCE it does have. One asked to be walked
# through a procedure when the corpus holds a one-line fix. One asked "can I"
# when the corpus states what the agent should do instead. v1 rule 5 made a
# partial answer a refusal, and the model read a shape mismatch as a partial
# answer.
#
# Reading the failing outputs showed a second thing. The model was not failing
# to read the corpus. It reached for the refusal template as a FIRST DRAFT,
# then reasoned in the open and answered correctly anyway:
#
#     "Wait, let me re-read the context blocks."
#     "I need to correct myself. The context does contain information about
#      ERR-7215."
#     "No wait, I need to follow the rules properly."
#
# The reply was the only place it could think. So v2 changes two things about
# refusing, and nothing else:
#
#   WHAT a refusal may be about. Missing FACTS only. Never the question's
#   wording, shape or level of detail. Rules 4 and 5.
#
#   WHEN the model decides. A decision step placed above the rules, so the
#   choice is made before the first word is written. Rule 6 then bans the
#   self-correction itself, naming the exact phrases the failures produced.
#
# Everything else is identical to v1. Citations, no outside knowledge, the
# fixed refusal string, and the ban on hedging all stay. The guard from Week 5
# is that correct refusals must not fall, so rule 4 still refuses hard when the
# facts genuinely are not there, and missed_refusal is tracked as a failure
# mode for exactly this reason.
SYSTEM_PROMPT_V2 = """You are a support-desk answering assistant for a help-centre corpus.

You answer ONLY from the CONTEXT BLOCKS given to you in the user message.
Each block is labelled with a chunk_id in square brackets, like [HC-4002-structured-007].

BEFORE YOU WRITE ANYTHING, decide. Read the CONTEXT BLOCKS and look for the
line that most directly addresses the question. A table row counts. A single
sentence counts. A rule stated as "Never do X" counts as the answer to "can I
do X".

  You found such a line      -> you MUST answer. Refusing is forbidden.
  You found no such line     -> refuse, using rule 4.

Decide once, then write once. Your first written word is already the decision,
so do not start writing until you have made it.

RULES. These are absolute. There is no situation in which you may break them.

1. Every single sentence of your answer MUST end with a citation naming the block
   it came from, written exactly as [chunk_id]. A sentence with no citation is a
   rule violation.
2. You may cite ONLY chunk_ids that appear in the CONTEXT BLOCKS below. Never
   invent, guess, abbreviate or reformat a chunk_id.
3. You may state ONLY facts that are written in the CONTEXT BLOCKS. You may not
   use outside knowledge. You may not infer. You may not generalise. You may not
   fill a gap with something that sounds reasonable.
4. A refusal is about MISSING FACTS, and nothing else. Refuse only when the
   CONTEXT BLOCKS do not contain the information the question needs. When you
   refuse, reply with exactly this, and nothing else:

REFUSED: The help-centre corpus does not contain this information.
Missing: <one short line naming what was asked for and not found>

5. Never refuse because of how the question is worded. If the CONTEXT BLOCKS
   hold the substance, answer, even when:
   - the question asks for steps and the context gives a single instruction,
   - the question asks "can I" and the context states what to do instead,
   - the question expects a long procedure and the context is one line,
   - the question uses different words for the same thing.
   An answer that covers the substance in fewer steps than the question expected
   is a complete answer, not a partial one. Say what the context says.
6. Your reply is EITHER a refusal OR an answer. Never both. Never write REFUSED
   and then keep going. Never write "wait", "actually", "hold on", "let me
   re-read", "I need to correct myself", or any other second thought. If you
   feel that urge, your first draft was wrong: write only the answer, and do
   not mention that you changed your mind.
7. Never apologise, never offer a workaround, never suggest what the answer
   might be, and never tell the user to check elsewhere.

You are measured on answering when the facts are there, and refusing when they
are not."""


_PROMPTS = {"v1": SYSTEM_PROMPT_V1, "v2": SYSTEM_PROMPT_V2}


def _active_prompt() -> str:
    """The grounding prompt this run uses.

    Resolved once at import, so prompt_fingerprint() in the trace config hashes
    whichever version is active. Switching it changes prompt_sha, which is the
    one difference run_evals --compare allows between two runs.
    """
    version = get_settings().prompt_version
    if version not in _PROMPTS:
        raise ValueError(f"Unknown prompt_version {version!r}. Expected one of {list(_PROMPTS)}.")
    return _PROMPTS[version]


SYSTEM_PROMPT = _active_prompt()

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
    mode: str
    answer: str
    refused: bool
    gate_fired: bool
    retrieved: list[dict] = field(default_factory=list)
    citations: list[Citation] = field(default_factory=list)
    context: str = ""
    # True when the provider refused the full request on budget and the context
    # had to be trimmed to get an answer at all. Set so a caller never presents
    # a budget-shrunk answer as a full-context one.
    budget_degraded: bool = False

    @property
    def all_citations_resolve(self) -> bool:
        return bool(self.citations) and all(c.resolves for c in self.citations)


def _llm(max_tokens: int | None = None):
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
        max_tokens=max_tokens or settings.max_tokens,
        timeout=120,
    )


# Provider messages that mean "your credit balance cannot cover this request".
# Matched on text because OpenRouter reports all of them as a single 402.
_BUDGET_MARKERS = (
    "requires more credits",
    "prompt tokens limit exceeded",
    "can only afford",
    "insufficient credits",
)

# Bound the retry ladder. Each step either shrinks the reply or drops the
# lowest-ranked context block, so a handful of steps covers the whole range.
_MAX_BUDGET_ATTEMPTS = 8

# Smallest reply budget that can still hold a VALID answer.
#
# A correct answer here is two sentences, each ending in a [chunk_id], which
# measures 120-140 tokens. Below that the model cannot comply, and because the
# prompt makes a partial answer a refusal, an under-budget call returns a
# CONFIDENT REFUSAL for a question the context answers perfectly well.
#
# That is the worst possible output: indistinguishable from a real
# out-of-corpus refusal, and wrong. So generation is declared unavailable below
# this floor rather than squeezed into producing a lie. Retrieval still answers
# the question for free.
_MIN_VIABLE_OUTPUT_TOKENS = 160


def _is_budget_error(exc: Exception) -> bool:
    """A 402: the balance cannot cover this request. Shrinking it may help."""
    text = str(exc).lower()
    return "402" in text and any(m in text for m in _BUDGET_MARKERS)


def _is_rate_limit_error(exc: Exception) -> bool:
    """A 429: too many requests. Shrinking the request does NOT help.

    Free models carry a daily request cap, separate from any credit balance.
    Once it is spent, every call fails until the window resets, no matter how
    small. Retrying is futile, so this must not enter the shrink-and-retry
    ladder that the 402 path uses.
    """
    text = str(exc).lower()
    return "429" in text and ("rate limit" in text or "rate-limited" in text)


def _rate_limit_reset(exc: Exception) -> str | None:
    """Human-readable reset time from the X-RateLimit-Reset header, if present."""
    match = re.search(r"X-RateLimit-Reset'?\s*:\s*'?(\d{10,13})", str(exc))
    if not match:
        return None
    import datetime as _dt

    stamp = int(match.group(1))
    seconds = stamp / 1000 if stamp > 10_000_000_000 else stamp
    when = _dt.datetime.fromtimestamp(seconds, _dt.timezone.utc).astimezone()
    hours = (seconds - _dt.datetime.now(_dt.timezone.utc).timestamp()) / 3600
    return f"{when.strftime('%Y-%m-%d %H:%M %Z')} (about {hours:.0f}h from now)"


def _is_generation_unavailable(exc: Exception) -> bool:
    """The provider will not answer, for quota reasons rather than a bug.

    Callers use this to degrade to retrieval-only instead of showing a stack
    trace. It covers both a spent credit balance and a spent request quota.
    """
    return _is_budget_error(exc) or _is_rate_limit_error(exc)


def _affordable_output(exc: Exception) -> int | None:
    """The output-token ceiling the provider just told us it can cover."""
    match = re.search(r"can only afford (\d+)", str(exc))
    return int(match.group(1)) if match else None


def _prompt_ceiling(exc: Exception) -> int | None:
    """The prompt-token ceiling from 'Prompt tokens limit exceeded: X > Y'."""
    match = re.search(r"prompt tokens limit exceeded:\s*\d+\s*>\s*(\d+)", str(exc), re.I)
    return int(match.group(1)) if match else None


def _invoke_within_budget(scored: list, question: str) -> tuple[str, int, bool]:
    """Answer using as much context as the remaining credit allows.

    The first attempt is the full retrieved context at the configured
    max_tokens, so a healthy account behaves exactly as before and the graded
    runs are unaffected.

    When the provider refuses on budget, the request is made smaller rather than
    the failure being handed to the caller. Two levers, in this order:

      1. Lower the reply cap to what the provider says it can afford. The reply
         is a couple of cited sentences, so this is usually enough.
      2. Drop the LOWEST-ranked context block and retry. Dropping from the tail
         keeps the best-matching chunks, which is where the answer almost always
         is.

    Returns (answer text, blocks actually used, whether it had to degrade).
    Raises the provider error if even a single block cannot be afforded, because
    at that point there is no answer worth returning.
    """
    settings = get_settings()
    blocks = list(scored)
    max_tokens = settings.max_tokens
    if max_tokens < _MIN_VIABLE_OUTPUT_TOKENS:
        # A configured cap below the floor cannot produce a compliant answer, so
        # it would turn every answerable question into a refusal. Raise it and
        # say so, rather than honouring a setting that can only produce wrong
        # output. Lower MAX_TOKENS if you want cheaper calls; this floor is what
        # the citation rules structurally require.
        logger.warning(
            "Configured max_tokens=%d is below the %d needed for a citable "
            "answer; using %d instead",
            max_tokens,
            _MIN_VIABLE_OUTPUT_TOKENS,
            _MIN_VIABLE_OUTPUT_TOKENS,
        )
        max_tokens = _MIN_VIABLE_OUTPUT_TOKENS
    degraded = False
    last_error: Exception | None = None

    for _ in range(_MAX_BUDGET_ATTEMPTS):
        if not blocks:
            break
        try:
            response = _llm(max_tokens=max_tokens).invoke(
                [
                    ("system", SYSTEM_PROMPT),
                    (
                        "human",
                        USER_TEMPLATE.format(
                            context=format_context(blocks), question=question
                        ),
                    ),
                ]
            )
            return (response.content or "").strip(), len(blocks), degraded
        except Exception as exc:
            if _is_rate_limit_error(exc):
                # No amount of shrinking beats a request-count cap. Fail fast so
                # the caller can degrade to retrieval instead of burning more
                # attempts against a quota that is already spent.
                raise
            if not _is_budget_error(exc):
                raise
            last_error = exc
            degraded = True

            affordable = _affordable_output(exc)
            if affordable is not None and affordable < max_tokens:
                if affordable < _MIN_VIABLE_OUTPUT_TOKENS:
                    # Do not squeeze. See _MIN_VIABLE_OUTPUT_TOKENS: the model
                    # would answer with a refusal it cannot justify.
                    logger.error(
                        "Credit allows only %d output tokens; %d are needed for a "
                        "citable answer. Declining to generate rather than return "
                        "an unjustified refusal.",
                        affordable,
                        _MIN_VIABLE_OUTPUT_TOKENS,
                    )
                    raise
                # Leave a little headroom; a reply truncated mid-citation is
                # worse than a slightly shorter one.
                max_tokens = max(_MIN_VIABLE_OUTPUT_TOKENS, affordable - 16)
                logger.warning(
                    "Lowering reply cap to %d tokens to fit the remaining credit",
                    max_tokens,
                )
                continue

            if _prompt_ceiling(exc) is not None or len(blocks) > 1:
                blocks = blocks[:-1]
                logger.warning(
                    "Prompt over budget; retrying with %d context block(s)",
                    len(blocks),
                )
                continue
            break

    raise last_error if last_error else RuntimeError("Generation failed")


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


def _gate_signal(scored: list, mode: str) -> float:
    """The number the relevance gate should judge, per retrieval mode.

    Dense mode returns a cosine relevance score, which the threshold was chosen
    for. Hybrid mode returns an RRF score, roughly 1/60 in magnitude, which
    would trip the gate on every single query. So in hybrid mode the gate reads
    the dense score that RRF carried through in metadata instead.
    """
    if not scored:
        return 0.0
    if mode == "dense":
        return max(float(s) for _, s in scored)
    return max(float(d.metadata.get("dense_score", 0.0)) for d, _ in scored)


def _clears_gate(scored: list, mode: str, threshold: float) -> bool:
    """Does anything retrieved deserve to reach the model?

    In hybrid mode a positive BM25 score also clears the gate. That is the point
    of adding the keyword arm: an exact match on a rare token like ERR-7208 is
    real evidence even when the vector arm is cold on it, and refusing there
    would throw away the very fix being measured.
    """
    if not scored:
        return False
    if _gate_signal(scored, mode) >= threshold:
        return True
    if mode == "hybrid":
        return any(float(d.metadata.get("keyword_score", 0.0)) > 0.0 for d, _ in scored)
    return False


def answer_question(
    question: str,
    strategy: str,
    *,
    k: int | None = None,
    product_area: str | None = None,
    use_gate: bool = True,
    mode: str | None = None,
) -> Answer:
    """Retrieve, then answer strictly from what was retrieved, or refuse.

    Args:
        use_gate: When True, refuse without calling the model if nothing clears
            settings.score_threshold. Set False to force the model itself to do
            the refusing, which is what the refusal transcripts demonstrate.
        mode: "dense" or "hybrid". Defaults to settings.retrieval_mode. This is
            the single knob Week 4 flips to produce its before-and-after.
    """
    settings = get_settings()
    mode = mode or settings.retrieval_mode
    from rag.hybrid import search_by_mode

    scored = search_by_mode(question, strategy, mode=mode, k=k, product_area=product_area)
    from rag.retriever import format_hits  # local import avoids a cycle at import time

    retrieved = format_hits(scored)

    if use_gate and not _clears_gate(scored, mode, settings.score_threshold):
        best = _gate_signal(scored, mode)
        return Answer(
            question=question,
            strategy=strategy,
            mode=mode,
            answer=(
                f"{REFUSAL_TOKEN}: The help-centre corpus does not contain this "
                f"information.\nMissing: nothing retrieved above the "
                f"{settings.score_threshold} relevance gate (best {mode} signal was {best:.4f})."
            ),
            refused=True,
            gate_fired=True,
            retrieved=retrieved,
        )

    context = format_context(scored)
    context_ids = {h["chunk_id"] for h in retrieved}

    text, blocks_used, degraded = _invoke_within_budget(scored, question)
    if degraded:
        # The context the model actually saw is what the citation check must be
        # judged against, so narrow both to the blocks that survived.
        scored = scored[:blocks_used]
        retrieved = retrieved[:blocks_used]
        context = format_context(scored)
        context_ids = {h["chunk_id"] for h in retrieved}

    return Answer(
        question=question,
        strategy=strategy,
        mode=mode,
        answer=text,
        refused=text.upper().startswith(REFUSAL_TOKEN),
        gate_fired=False,
        retrieved=retrieved,
        budget_degraded=degraded,
        citations=verify_citations(text, strategy, context_ids),
        context=context,
    )
