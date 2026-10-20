"""The cost improvement: answer the same question twice without paying twice.

THE CHEAPEST REQUEST IS THE ONE YOU NEVER SEND
    The log says this app costs about $0.00025 a request and spends roughly
    1,275 tokens on it. Prompt caching already happens at the provider, and is
    not ours to tune. The lever we own is whether the call is made at all.

    A support queue repeats itself. "What is the fix for ERR-4032" arrives
    again and again, worded differently each time. Those are the requests worth
    not sending.

TWO LAYERS
    EXACT     the same question, normalised. Free, instant, and never wrong.
    SIMILAR   the same question in different words. Cheap and explainable, and
              the one that can be wrong.

WHY WORD OVERLAP AND NOT EMBEDDINGS
    An embedding cache needs the embedding model loaded and a vector compared
    before you know whether you saved anything. On a corpus this size that is a
    real fraction of the cost you were trying to avoid.

    Word overlap is the same measure Week 8 used to catch a looping agent. It
    is explainable in one sentence, which matters here more than usual: when a
    cache serves the wrong answer, somebody has to be able to say why.

THE FENCE, WHICH MATTERS MORE THAN THE CACHE
    A cached answer is only valid under the settings that produced it. The key
    includes the model, the prompt fingerprint and the corpus fingerprint, so
    changing any of them empties the cache rather than serving six-week-old
    answers under a new prompt. Week 6 lost a measurement to exactly that kind
    of quiet staleness.

THE RISK, STATED PLAINLY
    A similarity cache can serve an answer to a question it does not actually
    answer. "What is the fix for ERR-4032" and "what is the fix for ERR-4044"
    share almost every word. That is not a hypothetical: it is the single most
    likely way this makes the app worse, and `measure.py` tests for it rather
    than hoping.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from config import get_settings

CACHE_FILE = "w11_answer_cache.json"

# Word overlap at or above this counts as the same question.
#
# 0.8 is deliberately stricter than the 0.5 Week 8 used to catch a looping
# agent. There, a false positive cost one wasted step. Here it costs a customer
# the wrong answer, so the threshold moves in the safe direction. Section 6 of
# the write-up measures what each setting would have served.
SIMILARITY = 0.8

_WORD_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

# Codes are identity, not vocabulary. "ERR-4032" and "ERR-4044" share every
# other word in their sentence, so a cache that treats a code as just another
# token will happily serve one for the other. Any difference in the codes a
# question names blocks a similarity hit outright.
_CODE_RE = re.compile(r"\b(?:ERR|MIG)-?\d{3,4}\b", re.IGNORECASE)


def normalise(question: str) -> str:
    return " ".join(_WORD_RE.findall((question or "").lower()))


def codes_in(question: str) -> set[str]:
    return {c.upper().replace("-", "") for c in _CODE_RE.findall(question or "")}


def similarity(a: str, b: str) -> float:
    wa, wb = set(normalise(a).split()), set(normalise(b).split())
    if not wa or not wb:
        return 0.0
    return len(wa & wb) / len(wa | wb)


def fence() -> str:
    """The settings a cached answer is only valid under."""
    from evals.w5_trace import corpus_fingerprint, prompt_fingerprint

    s = get_settings()
    return f"{s.openrouter_model}|{prompt_fingerprint()}|{corpus_fingerprint()}"


@dataclass
class Entry:
    question: str
    answer: str
    chunk_ids: list[str] = field(default_factory=list)
    citations: list[str] = field(default_factory=list)
    refused: bool = False
    trace_id: str = ""
    fence: str = ""
    hits: int = 0

    def as_dict(self) -> dict:
        return {
            "question": self.question,
            "answer": self.answer,
            "chunk_ids": self.chunk_ids,
            "citations": self.citations,
            "refused": self.refused,
            "trace_id": self.trace_id,
            "fence": self.fence,
            "hits": self.hits,
        }


@dataclass
class Lookup:
    """What the cache decided, and why."""

    entry: Entry | None = None
    kind: str = "miss"          # exact | similar | miss
    score: float = 0.0
    blocked_by: str = ""        # why a near-match was refused

    @property
    def hit(self) -> bool:
        return self.entry is not None


class AnswerCache:
    """Exact and similar lookup over answers already paid for."""

    def __init__(self, path: Path | None = None, *, similarity_threshold: float = SIMILARITY):
        self.path = path or (Path(get_settings().results_dir) / CACHE_FILE)
        self.threshold = similarity_threshold
        self.entries: list[Entry] = []
        self._exact: dict[str, Entry] = {}
        self.load()

    # -- storage ----------------------------------------------------------
    def load(self) -> None:
        if not self.path.exists():
            return
        try:
            rows = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        self.entries = [Entry(**r) for r in rows]
        self._reindex()

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps([e.as_dict() for e in self.entries], indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def _reindex(self) -> None:
        self._exact = {normalise(e.question): e for e in self.entries}

    # -- the decision -----------------------------------------------------
    def lookup(self, question: str, *, now_fence: str | None = None) -> Lookup:
        """Can this question be answered from something already paid for?"""
        current = now_fence or fence()
        valid = [e for e in self.entries if e.fence == current]
        if not valid:
            return Lookup(kind="miss")

        exact = self._exact.get(normalise(question))
        if exact is not None and exact.fence == current:
            return Lookup(entry=exact, kind="exact", score=1.0)

        asked_codes = codes_in(question)
        best, best_score, blocked = None, 0.0, ""
        for entry in valid:
            score = similarity(question, entry.question)
            if score < self.threshold:
                continue
            if codes_in(entry.question) != asked_codes:
                # Near-identical wording, different error code. This is the
                # exact near-miss that would hand a customer the fix for the
                # wrong problem.
                blocked = "a different error code"
                continue
            if score > best_score:
                best, best_score = entry, score

        if best is not None:
            return Lookup(entry=best, kind="similar", score=round(best_score, 3))
        return Lookup(kind="miss", blocked_by=blocked)

    def put(self, question: str, *, answer: str, chunk_ids: list[str],
            citations: list[str], refused: bool, trace_id: str = "") -> Entry:
        entry = Entry(
            question=question,
            answer=answer,
            chunk_ids=list(chunk_ids),
            citations=list(citations),
            refused=refused,
            trace_id=trace_id,
            fence=fence(),
        )
        self.entries.append(entry)
        self._exact[normalise(question)] = entry
        return entry

    def clear(self) -> None:
        self.entries.clear()
        self._exact.clear()
