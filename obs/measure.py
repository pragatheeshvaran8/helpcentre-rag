"""Cost per request, before and after, with the risk measured too.

HOW THE SAVING IS MEASURED
    Real traffic, replayed. The log holds every question this app has been
    asked. Replaying it in time order through a cold cache answers the only
    question that matters: how many of these would we not have had to send?

    No synthetic workload, no assumed hit rate. The questions are the ones that
    were actually asked, in the order they were actually asked.

WHY THE RISK IS MEASURED AT ALL
    A cache that serves the wrong answer is not a saving, it is a bug with a
    good dashboard. Week 8 learned that a fix which only reports its wins is
    not a fix you can trust.

    So `risk()` takes the Week 7 tickets, whose correct answers are known and
    written down, and asks: if the cache had served ticket A's answer for
    ticket B, would B's requirements still be met? Every served answer that
    fails its own ticket's requirements is counted and named.

THE NUMBER THAT DECIDES IT
    Not the hit rate. A 90% hit rate that serves one wrong refund answer is
    worse than a 30% hit rate that never does. The verdict is: saving, and
    wrong answers served. Both, every time.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from obs import store
from obs.cache import AnswerCache, Lookup


@dataclass
class Replay:
    """What replaying the log through a cache would have cost."""

    requests: int = 0
    exact_hits: int = 0
    similar_hits: int = 0
    misses: int = 0
    blocked: int = 0

    tokens_without_cache: int = 0
    tokens_with_cache: int = 0
    cost_without_cache: float = 0.0
    cost_with_cache: float = 0.0
    calls_without_cache: int = 0
    calls_with_cache: int = 0

    served: list[dict] = field(default_factory=list)

    @property
    def hits(self) -> int:
        return self.exact_hits + self.similar_hits

    @property
    def hit_rate(self) -> float:
        return round(self.hits / self.requests, 4) if self.requests else 0.0

    @property
    def token_saving(self) -> float:
        if not self.tokens_without_cache:
            return 0.0
        return round(1 - self.tokens_with_cache / self.tokens_without_cache, 4)

    @property
    def cost_saving(self) -> float:
        if not self.cost_without_cache:
            return 0.0
        return round(1 - self.cost_with_cache / self.cost_without_cache, 4)

    def as_dict(self) -> dict:
        return {
            "requests": self.requests,
            "exact_hits": self.exact_hits,
            "similar_hits": self.similar_hits,
            "misses": self.misses,
            "blocked_near_misses": self.blocked,
            "hit_rate": self.hit_rate,
            "cost_per_request_before": round(
                self.cost_without_cache / self.requests, 8) if self.requests else 0.0,
            "cost_per_request_after": round(
                self.cost_with_cache / self.requests, 8) if self.requests else 0.0,
            "tokens_per_request_before": round(
                self.tokens_without_cache / self.requests, 1) if self.requests else 0.0,
            "tokens_per_request_after": round(
                self.tokens_with_cache / self.requests, 1) if self.requests else 0.0,
            "calls_before": self.calls_without_cache,
            "calls_after": self.calls_with_cache,
            "token_saving": self.token_saving,
            "cost_saving": self.cost_saving,
        }


def replay(rows: list[dict] | None = None, *, threshold: float | None = None) -> Replay:
    """Replay real traffic through a cold cache, in the order it arrived."""
    rows = store.read_all() if rows is None else rows
    rows = sorted(rows, key=lambda r: r.get("at", ""))

    cache = AnswerCache(path=_scratch_path())
    cache.clear()
    if threshold is not None:
        cache.threshold = threshold

    # Backfilled traces carry no fence of their own, so they are all treated as
    # having been produced under today's settings. That is what makes this a
    # fair upper bound on the saving rather than a guess: it assumes nothing
    # expired, which is the best case the cache can possibly have.
    current = cache_fence_for_replay()

    out = Replay()
    for row in rows:
        question = row.get("question") or ""
        if not question:
            continue
        out.requests += 1
        tokens = int(row.get("total_tokens", 0))
        cost = float(row.get("cost", 0.0))
        calls = int(row.get("llm_calls", 0))

        out.tokens_without_cache += tokens
        out.cost_without_cache += cost
        out.calls_without_cache += calls

        found: Lookup = cache.lookup(question, now_fence=current)
        if found.hit:
            if found.kind == "exact":
                out.exact_hits += 1
            else:
                out.similar_hits += 1
            found.entry.hits += 1
            out.served.append(
                {
                    "asked": question,
                    "served_from": found.entry.question,
                    "kind": found.kind,
                    "score": found.score,
                    "answer": found.entry.answer,
                    "trace_id": row.get("trace_id"),
                }
            )
            continue

        if found.blocked_by:
            out.blocked += 1
        out.misses += 1
        out.tokens_with_cache += tokens
        out.cost_with_cache += cost
        out.calls_with_cache += calls

        entry = cache.put(
            question,
            answer=row.get("answer", ""),
            chunk_ids=row.get("chunk_ids") or [],
            citations=row.get("citations") or [],
            refused=bool(row.get("refused")),
            trace_id=row.get("trace_id", ""),
        )
        entry.fence = current

    return out


def cache_fence_for_replay() -> str:
    return "replay"


def _scratch_path():
    from pathlib import Path

    from config import get_settings

    return Path(get_settings().results_dir) / "w11_replay_cache.json"


# ---------------------------------------------------------------------------
@dataclass
class Risk:
    """What the cache would have got WRONG, which is the number that decides it."""

    served: int = 0
    wrong: int = 0
    cases: list[dict] = field(default_factory=list)

    @property
    def wrong_rate(self) -> float:
        return round(self.wrong / self.served, 4) if self.served else 0.0

    def as_dict(self) -> dict:
        return {
            "answers_served_from_cache": self.served,
            "wrong_answers_served": self.wrong,
            "wrong_rate": self.wrong_rate,
            "cases": self.cases[:10],
        }


def risk(*, threshold: float | None = None) -> Risk:
    """Would a cached answer still satisfy the ticket it was served for?

    Uses the Week 7 tickets, because their correct answers are written down as
    `must_contain` strings against named articles. A served answer that does
    not satisfy the asking ticket's own requirements is a wrong answer, and it
    is counted whether or not it looks plausible.
    """
    from evals.w7_tickets import ticket_set
    from rag.retriever import chunk_answers_question

    cache = AnswerCache(path=_scratch_path())
    cache.clear()
    if threshold is not None:
        cache.threshold = threshold
    current = cache_fence_for_replay()

    out = Risk()
    tickets = ticket_set()

    # Fill the cache from every ticket's own correct answer first, so a hit is
    # always a hit on a DIFFERENT ticket. That is the dangerous case.
    for ticket in tickets:
        entry = cache.put(
            ticket["question"],
            answer=f"[answer for {ticket['id']}]",
            chunk_ids=[],
            citations=[],
            refused=False,
            trace_id=ticket["id"],
        )
        entry.fence = current
        entry.question = ticket["question"]

    for ticket in tickets:
        # Ask a reworded version of each ticket and see what comes back.
        for variant in _rewordings(ticket["question"]):
            found = cache.lookup(variant, now_fence=current)
            if not found.hit:
                continue
            out.served += 1
            source_id = found.entry.trace_id
            if source_id == ticket["id"]:
                continue  # served its own answer: correct
            out.wrong += 1
            out.cases.append(
                {
                    "asked": variant,
                    "which_ticket": ticket["id"],
                    "served_from": source_id,
                    "kind": found.kind,
                    "score": found.score,
                }
            )
    return out


def _rewordings(question: str) -> list[str]:
    """Small, realistic rewordings of the same question.

    Not paraphrases from a model. A support agent retyping a question changes
    punctuation and filler, not meaning, and that is the traffic a cache is
    supposed to catch.
    """
    base = question.strip()
    return [
        base,
        base.replace("?", "").strip(),
        f"hi, {base[0].lower()}{base[1:]}",
        base.replace("Customer", "The customer").replace("customer", "client"),
    ]
