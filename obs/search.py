"""The support drill: finding one bad answer from a vague complaint.

THE SITUATION THIS IS BUILT FOR
    A customer says: "someone asked about a refund last week and your thing
    told them the wrong thing." That is everything you get. No trace id, no
    timestamp, no exact wording, and the word they remember ("refund") may not
    even be the word the question used.

    `by_id` in store.py handles the easy case. This file handles the real one.

HOW IT NARROWS
    Filters first, ranking second. Filters are exact and cheap: a date range, a
    runner, whether it refused, a cost floor. They turn thousands into dozens
    without any judgement.

    Ranking is applied to what survives. It scores a trace against the words a
    complaint actually contains, looking in the question AND the answer,
    because a complaint paraphrases both and quotes neither.

WHY NOT EMBEDDINGS
    A support drill has to be fast and explainable. A support engineer who
    cannot say WHY a trace came top cannot defend handing it to an angry
    customer. Word overlap with an IDF weighting is explainable in one line,
    runs over the whole log in milliseconds, and needs no model.

    "Quickly" is one of the four things the mentor checks, and loading an
    embedding model to search a log is not quick.

WHAT A HIT CARRIES
    The matched trace, the score, and the words that earned it. The last one
    matters: it is the difference between "the system says this one" and "this
    one, because it is the only refund answer that week that cited nothing".
"""
from __future__ import annotations

import math
import re
import time
from dataclasses import dataclass, field

from obs import store

_WORD_RE = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")

# Words a complaint always contains and which identify nothing.
_STOP = {
    "the", "a", "an", "and", "or", "but", "is", "was", "were", "it", "its",
    "they", "them", "their", "we", "our", "you", "your", "i", "me", "my",
    "to", "of", "in", "on", "for", "with", "about", "that", "this", "these",
    "said", "say", "says", "told", "asked", "ask", "got", "gave", "give",
    "something", "someone", "somebody", "thing", "wrong", "bad", "last",
    "week", "yesterday", "day", "days", "ago", "customer", "agent", "answer",
    "question", "did", "do", "does", "not", "no", "one", "some", "what",
}


def words(text: str) -> list[str]:
    return [w for w in _WORD_RE.findall((text or "").lower()) if w not in _STOP]


@dataclass
class Hit:
    """One candidate, with the reason it is a candidate."""

    trace: dict
    score: float
    matched: list[str] = field(default_factory=list)
    why: str = ""

    @property
    def trace_id(self) -> str:
        return self.trace.get("trace_id", "?")

    def line(self) -> str:
        t = self.trace
        flags = []
        if t.get("refused"):
            flags.append("refused")
        if not t.get("citations"):
            flags.append("NO CITATIONS")
        if t.get("cache_hit"):
            flags.append("cache hit")
        return (
            f"{self.trace_id}  {t.get('at','')[:19]}  score {self.score:5.2f}  "
            f"{'[' + ', '.join(flags) + '] ' if flags else ''}"
            f"{' '.join((t.get('question') or '').split())[:70]}"
        )


def _idf(rows: list[dict]) -> dict:
    """How rare each word is across the log.

    Without this, "invoice" and "refund" weigh the same in a corpus about
    invoices, and every trace matches. IDF is what makes the rare word the one
    that finds the needle.
    """
    seen: dict[str, int] = {}
    for row in rows:
        blob = set(words(row.get("question", "")) + words(row.get("answer", "")))
        for w in blob:
            seen[w] = seen.get(w, 0) + 1
    n = max(1, len(rows))
    return {w: math.log(1 + n / c) for w, c in seen.items()}


def search(
    complaint: str = "",
    *,
    since: str | None = None,
    until: str | None = None,
    runner: str | None = None,
    refused: bool | None = None,
    uncited: bool | None = None,
    min_cost: float | None = None,
    mentions_chunk: str | None = None,
    limit: int = 10,
    rows: list[dict] | None = None,
) -> tuple[list[Hit], dict]:
    """Narrow by filters, then rank by the complaint's rare words.

    Returns the hits and a small report of how the funnel narrowed, because
    showing the narrowing is how a drill is explained to anyone else.
    """
    started = time.perf_counter()
    rows = store.read_all(since=since, until=until) if rows is None else list(rows)
    total = len(rows)

    steps = [("all traces", total)]

    if runner is not None:
        rows = [r for r in rows if r.get("runner") == runner]
        steps.append((f"runner == {runner}", len(rows)))
    if refused is not None:
        rows = [r for r in rows if bool(r.get("refused")) == refused]
        steps.append((f"refused == {refused}", len(rows)))
    if uncited is not None:
        rows = [r for r in rows if (not r.get("citations")) == uncited]
        steps.append((f"uncited == {uncited}", len(rows)))
    if min_cost is not None:
        rows = [r for r in rows if r.get("cost", 0.0) >= min_cost]
        steps.append((f"cost >= {min_cost}", len(rows)))
    if mentions_chunk:
        rows = [
            r for r in rows
            if mentions_chunk in (r.get("chunk_ids") or [])
            or mentions_chunk in (r.get("citations") or [])
        ]
        steps.append((f"touched {mentions_chunk}", len(rows)))

    hits: list[Hit] = []
    if complaint.strip():
        idf = _idf(rows) if rows else {}
        terms = set(words(complaint))
        for row in rows:
            blob = set(words(row.get("question", "")) + words(row.get("answer", "")))
            matched = sorted(terms & blob, key=lambda w: -idf.get(w, 0.0))
            if not matched:
                continue
            score = sum(idf.get(w, 0.0) for w in matched)
            hits.append(Hit(trace=row, score=round(score, 3), matched=matched[:6]))
        hits.sort(key=lambda h: -h.score)
        steps.append((f"matched any of {len(terms)} complaint word(s)", len(hits)))
    else:
        hits = [Hit(trace=r, score=0.0) for r in rows]

    elapsed_ms = round((time.perf_counter() - started) * 1000, 1)
    return hits[:limit], {
        "searched": total,
        "returned": min(len(hits), limit),
        "ms": elapsed_ms,
        "funnel": steps,
    }


def suspicious(rows: list[dict] | None = None) -> list[Hit]:
    """Traces worth a second look, with no complaint to go on at all.

    A bad answer usually leaves one of these marks. This is what you reach for
    when the complaint is too vague even to supply a search word.
    """
    rows = store.read_all() if rows is None else rows
    out: list[Hit] = []
    for row in rows:
        reasons = []
        if not row.get("refused") and not row.get("citations"):
            reasons.append("answered with no citation")
        if row.get("error"):
            reasons.append("recorded an error")
        answer = (row.get("answer") or "").upper()
        if answer.startswith("REFUSED") and len(answer.splitlines()) > 3:
            reasons.append("refused and then kept talking")
        if row.get("refused") and row.get("chunk_ids"):
            reasons.append("refused despite retrieving something")
        if reasons:
            out.append(Hit(trace=row, score=float(len(reasons)), why="; ".join(reasons)))
    out.sort(key=lambda h: -h.score)
    return out
