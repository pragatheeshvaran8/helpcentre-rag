"""Turn the cached runs of Weeks 7 to 10 into a trace log.

WHY BACKFILL AND NOT GENERATE
    The support drill needs a haystack. Generating a few hundred fresh requests
    would cost several days of free-tier quota and would produce traffic nobody
    ever actually sent.

    Weeks 7 to 10 already left about a hundred real runs on disk: real
    questions, real answers, real chunk ids, real token counts. Replaying them
    into the log costs nothing and makes the drill a search over things that
    genuinely happened.

WHAT IS INVENTED, AND WHAT IS NOT
    INVENTED: the timestamps. The caches record no wall-clock date, so each run
    is spread over the preceding fortnight at a plausible hour. The drill turns
    on narrowing by date, so the dates have to exist.

    NOT INVENTED: everything else. Question, answer, chunk ids, citations,
    refusal, token counts, per-call timings and the config all come from the
    cached record.

    Every backfilled trace carries `"backfilled": true` in its config, so a
    reader can tell a replayed run from a live one. A log that quietly mixes
    the two is worse than no log.
"""
from __future__ import annotations

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config import get_settings
from obs import store
from obs.trace import Trace, new_trace_id

# Fixed, so the same cache always produces the same log. A drill whose haystack
# reshuffles on every run is not a drill you can hand to somebody else.
SEED = 20261013

# Where the cached runs live, and what each one was.
SOURCES = [
    ("w7_race/agent__runs.json", "agent"),
    ("w7_race/workflow__runs.json", "workflow"),
    ("w8_runs/tickets_unfixed.json", "agent"),
    ("w8_runs/tickets_fixed.json", "agent"),
    ("w8_runs/attacks_undefended.json", "agent"),
    ("w8_runs/attacks_defended.json", "agent"),
    ("w10_runs/single__runs.json", "agent"),
    ("w10_runs/squad__runs.json", "squad"),
]


def _records() -> list[tuple[str, dict]]:
    """Every cached run on disk, with the runner that produced it."""
    base = Path(get_settings().results_dir)
    out = []
    for rel, runner in SOURCES:
        path = base / rel
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        for key, record in data.items():
            if isinstance(record, dict) and record.get("question"):
                out.append((runner, dict(record, _source=f"{rel}:{key}")))
    return out


def _spans_from(record: dict) -> list[dict]:
    """Rebuild per-step spans from whatever the cache kept.

    Week 10 runs carry a full per-call meter. Weeks 7 and 8 predate it and only
    have a call count and a total elapsed time, so their spans are evenly
    divided. That is an approximation and it is labelled as one, because a span
    that looks measured but was shared out is a lie about where the time went.
    """
    meter = record.get("meter") or {}
    per_call = meter.get("per_call") or []
    if per_call:
        return [
            {
                "name": f"{c.get('who','agent')}:{c.get('purpose','call')}",
                "ms": round(float(c.get("seconds", 0.0)) * 1000, 1),
                "input_tokens": int(c.get("input_tokens", 0)),
                "output_tokens": int(c.get("output_tokens", 0)),
                "cost": 0.0,
                "detail": c.get("purpose", ""),
                "ok": True,
                "measured": True,
            }
            for c in per_call
        ]

    calls = max(1, int(record.get("llm_calls", 1)))
    total_ms = float(record.get("elapsed_s", 0.0)) * 1000
    steps = record.get("steps") or []
    spans = []
    for i in range(calls):
        tool = steps[i].get("tool") if i < len(steps) and isinstance(steps[i], dict) else "step"
        spans.append(
            {
                "name": f"agent:{tool or 'step'}",
                "ms": round(total_ms / calls, 1),
                "input_tokens": 0,
                "output_tokens": 0,
                "cost": 0.0,
                "detail": "time divided evenly, not measured per step",
                "ok": True,
                "measured": False,
            }
        )
    return spans


def build(*, days_back: int = 14, overwrite: bool = False) -> dict:
    """Write the backfilled log. Returns a small summary."""
    from agent.meter import USD_PER_MILLION_INPUT, USD_PER_MILLION_OUTPUT

    if overwrite:
        for path in Path(get_settings().results_dir).glob(f"{store.LOG_DIR}/traces-*.jsonl"):
            path.unlink()

    rng = random.Random(SEED)
    records = _records()
    rng.shuffle(records)

    now = datetime.now(timezone.utc).replace(microsecond=0)
    written, by_day = 0, {}

    for runner, record in records:
        # A plausible working hour on a plausible day. Dates are invented; the
        # drill needs them and the cache has none.
        at = now - timedelta(
            days=rng.randint(1, days_back),
            hours=rng.randint(0, 10),
            minutes=rng.randint(0, 59),
        )
        at = at.replace(hour=rng.randint(8, 18))

        spans = _spans_from(record)
        for span in spans:
            span["cost"] = round(
                span["input_tokens"] / 1_000_000 * USD_PER_MILLION_INPUT
                + span["output_tokens"] / 1_000_000 * USD_PER_MILLION_OUTPUT,
                8,
            )

        trace = Trace(
            trace_id=new_trace_id(),
            at=at.isoformat(),
            question=record["question"],
            answer=record.get("answer", ""),
            runner=record.get("runner") or runner,
            refused=bool(record.get("refused")),
            chunk_ids=[c.get("chunk_id") for c in (record.get("retrieved") or []) if c.get("chunk_id")],
            citations=[
                c.get("chunk_id") for c in (record.get("citations") or []) if c.get("resolves")
            ],
            config={
                "backfilled": True,
                "source": record.get("_source", ""),
                "runner": record.get("runner") or runner,
                "stop_reason": record.get("stop_reason"),
            },
            error=record.get("error"),
        )
        # Spans are already closed dicts here, so they go on directly.
        row = trace.as_dict()
        row["spans"] = spans
        row["ms"] = round(sum(s["ms"] for s in spans), 1)
        row["input_tokens"] = sum(s["input_tokens"] for s in spans)
        row["output_tokens"] = sum(s["output_tokens"] for s in spans)
        row["total_tokens"] = row["input_tokens"] + row["output_tokens"]
        row["cost"] = round(sum(s["cost"] for s in spans), 8)
        row["llm_calls"] = sum(1 for s in spans if s["input_tokens"] or s["output_tokens"]) or len(spans)

        store.write(row)
        written += 1
        by_day[at.date().isoformat()] = by_day.get(at.date().isoformat(), 0) + 1

    return {
        "written": written,
        "days": len(by_day),
        "sources": len({r.get("_source", "").split(":")[0] for _, r in records}),
        "per_day": dict(sorted(by_day.items())),
    }
