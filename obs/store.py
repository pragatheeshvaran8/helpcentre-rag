"""Where traces go, and how they come back.

WHY JSONL AND NOT A DATABASE
    One line per request, appended, never rewritten. A crash mid-write loses
    one line rather than the file. `tail -f` works. `grep` works. Any tool that
    reads lines works, including ones nobody has written yet.

    A real deployment would ship these to LangSmith, Phoenix or an
    OpenTelemetry collector. The shape here is the same shape those take: a
    trace with spans under it. Swapping the sink is a change to this file and
    nothing else, which is the point of putting it in its own file.

WHY THE FILE IS DATED
    `traces-2026-10-13.jsonl`. A vague complaint always carries a rough date
    and almost never a trace id, so the date is the first filter a support
    drill reaches for. Sharding by day makes that filter free.

WHAT IS DELIBERATELY NOT HERE
    No rotation, no retention policy, no PII redaction. All three are real
    production concerns and all three are outside a week about finding one bad
    answer. Section 9 of the write-up says so rather than leaving it implied.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from config import get_settings

LOG_DIR = "w11_traces"


def _dir() -> Path:
    path = Path(get_settings().results_dir) / LOG_DIR
    path.mkdir(parents=True, exist_ok=True)
    return path


def _path_for(at: str | None = None) -> Path:
    """One file per UTC day, named by date."""
    day = (at or datetime.now(timezone.utc).isoformat())[:10]
    return _dir() / f"traces-{day}.jsonl"


def write(trace) -> Path:
    """Append one trace. Returns the file it landed in."""
    record = trace.as_dict() if hasattr(trace, "as_dict") else dict(trace)
    path = _path_for(record.get("at"))
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def read_all(since: str | None = None, until: str | None = None) -> list[dict]:
    """Every trace, oldest first, optionally bounded by ISO date.

    A malformed line is skipped rather than fatal. A log that cannot be read
    because one writer crashed mid-line is worse than a log with a gap.
    """
    rows: list[dict] = []
    for path in sorted(_dir().glob("traces-*.jsonl")):
        day = path.stem.replace("traces-", "")
        if since and day < since[:10]:
            continue
        if until and day > until[:10]:
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    rows.sort(key=lambda r: r.get("at", ""))
    return rows


def by_id(trace_id: str) -> dict | None:
    """The easy case: somebody quoted the trace id."""
    for row in read_all():
        if row.get("trace_id") == trace_id:
            return row
    return None


def days() -> list[str]:
    return sorted(p.stem.replace("traces-", "") for p in _dir().glob("traces-*.jsonl"))


def stats(rows: list[dict] | None = None) -> dict:
    """Headline numbers over a set of traces, for the cost report."""
    rows = read_all() if rows is None else rows
    if not rows:
        return {"n": 0}

    costs = sorted(r.get("cost", 0.0) for r in rows)
    tokens = sorted(r.get("total_tokens", 0) for r in rows)
    latencies = sorted(r.get("ms", 0.0) for r in rows)

    def pct(values: list, p: float):
        if not values:
            return 0
        # Nearest-rank. On a few hundred rows this is the honest reading, and
        # it never invents a value that no request actually had.
        i = min(len(values) - 1, max(0, int(round(p * len(values))) - 1))
        return values[i]

    hits = sum(1 for r in rows if r.get("cache_hit"))
    return {
        "n": len(rows),
        "days": sorted({r.get("at", "")[:10] for r in rows}),
        "cost_total": round(sum(costs), 6),
        "cost_per_request": round(sum(costs) / len(rows), 8),
        "cost_p50": pct(costs, 0.50),
        "cost_p95": pct(costs, 0.95),
        "tokens_total": sum(tokens),
        "tokens_per_request": round(sum(tokens) / len(rows), 1),
        "ms_p50": pct(latencies, 0.50),
        "ms_p95": pct(latencies, 0.95),
        "llm_calls": sum(r.get("llm_calls", 0) for r in rows),
        "cache_hits": hits,
        "cache_hit_rate": round(hits / len(rows), 4),
        "refusals": sum(1 for r in rows if r.get("refused")),
    }
