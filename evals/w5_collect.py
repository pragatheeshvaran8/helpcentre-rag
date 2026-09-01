"""Week 5 step 1: collect the 20 traces and write them out to be read by hand.

    python -m evals.w5_collect            # collect what is missing, then write
    python -m evals.w5_collect --force    # re-run every trace from scratch
    python -m evals.w5_collect --only P40 # one question (use with --force)
    python -m evals.w5_collect --render   # rewrite the files, run nothing

WHY IT IS RESUMABLE
    Twenty traces is twenty paid calls against a free model with a daily request
    cap. Losing nineteen good traces because the twentieth hit the cap is not
    acceptable, and re-running the nineteen would change them. So every trace is
    appended to a JSONL file the moment it completes, and a later run picks up
    only what is missing.

    A trace whose generation call failed is stored with an ``error`` and an
    outcome of ``error``, never as a failure. The provider running out of quota
    is not the app being wrong, and mixing the two would inflate the error
    analysis with somebody else's problem.

OUTPUT
    results/w5_traces.jsonl   append-only, one trace per line, the raw record
    results/w5_traces.json    the 20 traces in draw order, machine-readable
    results/w5_traces.md      the same traces laid out to be read by a person

    The markdown file is the one that matters. It is what the open coding in
    evals/w5_notes.py was written from.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from config import get_settings
from evals.w5_sample import W5_SAMPLE_SIZE, W5_SEED, audit_table, draw
from evals.w5_trace import missing_fields, run_trace

RESULTS = Path(get_settings().results_dir)
JSONL_PATH = RESULTS / "w5_traces.jsonl"
JSON_PATH = RESULTS / "w5_traces.json"
MD_PATH = RESULTS / "w5_traces.md"

# How much of a chunk to show in the readable file. Enough to judge whether the
# chunk answers the question, short enough that 20 traces stay readable.
PREVIEW_CHARS = 420

# Seconds to wait between generation calls.
#
# The free tier allows 20 requests a minute. Twenty traces back to back sit
# exactly on that line and the first run lost three of them to a 429. Waiting
# four seconds holds the rate at 15 a minute, which costs about a minute over
# the whole run and removes the failure mode entirely.
CALL_SPACING_SECONDS = 4.0


def _load_jsonl() -> dict[str, dict]:
    """Traces collected so far, newest wins, keyed by question id."""
    if not JSONL_PATH.exists():
        return {}
    found: dict[str, dict] = {}
    for line in JSONL_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        record = json.loads(line)
        found[record["question_id"]] = record
    return found


def _is_settled(trace: dict) -> bool:
    """Is this trace finished, or does it need running again?

    A trace whose generation call died on a provider rate limit is not a
    result. Re-running the collector retries exactly those and leaves every
    real outcome alone, so a run interrupted by a quota picks up where it
    stopped without disturbing the traces that already succeeded.
    """
    return trace.get("grading", {}).get("outcome") != "error"


def _append_jsonl(trace: dict) -> None:
    with JSONL_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(trace, ensure_ascii=False) + "\n")


def collect(
    force: bool = False,
    only: str | None = None,
    spacing: float = CALL_SPACING_SECONDS,
) -> list[dict]:
    """Run whatever is missing and return all 20 traces in draw order."""
    sample = draw()
    done = {} if force else _load_jsonl()

    for index, question in enumerate(sample, start=1):
        if only and question["id"] != only:
            continue
        if question["id"] in done and not force and _is_settled(done[question["id"]]):
            print(f"  {question['id']}  already collected, skipping")
            continue
        if question["id"] in done and not _is_settled(done[question["id"]]):
            print(f"  {question['id']}  previous call errored, retrying")
        trace_id = f"T{index:02d}"
        print(f"  {question['id']}  running as {trace_id} ...", flush=True)
        trace = run_trace(question, trace_id=trace_id, draw_index=index)
        _append_jsonl(trace)
        done[question["id"]] = trace
        outcome = trace["grading"]["outcome"]
        note = trace["generation"]["error"] or outcome
        print(f"        -> {note}")
        if spacing:
            time.sleep(spacing)

    return [done[q["id"]] for q in sample if q["id"] in done]


def _hit_line(hit: dict, satisfies: list[int]) -> str:
    arms = ""
    if "dense_rank" in hit or "keyword_rank" in hit:
        arms = f" [dense #{hit.get('dense_rank') or '-'}  bm25 #{hit.get('keyword_rank') or '-'}]"
    mark = f" **<- meets requirement {', '.join(str(i + 1) for i in satisfies)}**" if satisfies else ""
    return (
        f"{hit['rank']}. `{hit['chunk_id']}` ({hit['article_id']} / {hit['product_area']}) "
        f"score {hit['score']}{arms}{mark}"
    )


def _render_trace(trace: dict) -> str:
    g = trace["grading"]
    gen = trace["generation"]
    lines: list[str] = []

    lines.append(f"### {trace['trace_id']} — {trace['question_id']} · `{trace['kind']}`")
    lines.append("")
    lines.append(f"**Question:** {trace['question']}")
    lines.append("")
    lines.append(
        f"**Expected:** {trace['expected_behaviour']} · "
        f"**Outcome:** {g['outcome'].upper()} · "
        f"retrieval_ok {g['retrieval_ok']} · answer_ok {g['answer_ok']}"
    )
    lines.append("")

    if trace["requirements"]:
        lines.append("**What a correct answer must contain**")
        lines.append("")
        for i, status in enumerate(g["requirement_status"], start=1):
            got_r = ", ".join(f"`{c}`" for c in status["retrieved_by"]) or "**nothing**"
            got_c = ", ".join(f"`{c}`" for c in status["cited_by"]) or "**nothing**"
            need = " + ".join(f'"{s}"' for s in status["must_contain"])
            lines.append(f"{i}. {status['article_id']}: {need}")
            lines.append(f"   - retrieved by: {got_r}")
            lines.append(f"   - cited by: {got_c}")
        lines.append("")

    lines.append(f"**Retrieved (top {trace['config']['k']})**")
    lines.append("")
    for hit in trace["retrieval"]["hits"]:
        satisfies = [
            i
            for i, status in enumerate(g["requirement_status"])
            if hit["chunk_id"] in status["retrieved_by"]
        ]
        lines.append(_hit_line(hit, satisfies))
        body = " ".join(hit["text"].split())
        preview = body if len(body) <= PREVIEW_CHARS else body[:PREVIEW_CHARS] + " ..."
        lines.append("")
        lines.append(f"   > {preview}")
        lines.append("")

    lines.append("**Answer**")
    lines.append("")
    if gen["error"]:
        lines.append(f"```\nGENERATION FAILED: {gen['error']}\n```")
    else:
        lines.append("```")
        lines.append(gen["raw_answer"].strip() or "(empty)")
        lines.append("```")
    lines.append("")

    flags = []
    if gen["refused"]:
        flags.append("refused")
    if gen["gate_fired"]:
        flags.append("refused by the gate, model never called")
    if gen["budget_degraded"]:
        flags.append("context trimmed for budget")
    lines.append(f"**Flags:** {', '.join(flags) if flags else 'none'}")
    lines.append("")

    if trace["citations"]:
        cites = ", ".join(
            f"`{c['chunk_id']}`{'' if c['resolves'] else ' **DOES NOT RESOLVE**'}"
            f"{'' if c['was_in_context'] else ' **NOT IN CONTEXT**'}"
            for c in trace["citations"]
        )
    else:
        cites = "none"
    lines.append(f"**Citations:** {cites}")
    lines.append("")
    lines.append(f"**Replay:** `{trace['replay']}`")
    lines.append("")
    lines.append("---")
    return "\n".join(lines)


def render(traces: list[dict]) -> str:
    settings = get_settings()
    config = traces[0]["config"] if traces else {}

    counts: dict[str, int] = {}
    for t in traces:
        counts[t["grading"]["outcome"]] = counts.get(t["grading"]["outcome"], 0) + 1

    head = [
        "# Week 5 — the 20 traces, as collected",
        "",
        "Raw material for the error analysis. Nothing here is grouped or named.",
        "Grading is pass/fail only, by the rule in [`evals/w5_trace.py`](../evals/w5_trace.py).",
        "",
        "> **The corpus and the question pool are both invented.** See the README.",
        "",
        "## How this sample was drawn",
        "",
        audit_table(),
        "",
        "## The machinery, identical for all 20",
        "",
        "| Setting | Value |",
        "|---|---|",
    ]
    for key in (
        "strategy", "collection", "retrieval_mode", "k", "score_threshold",
        "embedding_model", "chunk_count", "rrf_k", "bm25_k1", "bm25_b",
        "llm_model", "llm_temperature", "llm_max_tokens", "prompt_sha", "corpus_sha",
    ):
        head.append(f"| `{key}` | `{config.get(key)}` |")

    head += [
        "",
        "Every trace carries its own copy of this table, so a trace stays true to "
        "the run that produced it even after `config.py` changes.",
        "",
        "## Outcome counts",
        "",
        "| Outcome | Traces |",
        "|---|---|",
    ]
    for outcome in ("pass", "fail", "error"):
        head.append(f"| {outcome} | {counts.get(outcome, 0)} |")
    head += ["| **total** | **" + str(len(traces)) + "** |", "", "---", ""]

    body = [_render_trace(t) for t in traces]
    return "\n".join(head) + "\n" + "\n".join(body) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect the Week 5 traces.")
    parser.add_argument("--force", action="store_true", help="re-run even if collected")
    parser.add_argument("--only", help="collect a single pool question id, e.g. P40")
    parser.add_argument("--render", action="store_true", help="rewrite files, run nothing")
    parser.add_argument(
        "--delay",
        type=float,
        default=CALL_SPACING_SECONDS,
        help="seconds between generation calls, to stay under the free per-minute cap",
    )
    args = parser.parse_args()

    print(f"Week 5 traces: {W5_SAMPLE_SIZE} drawn from the pool with seed {W5_SEED}")

    if args.render:
        done = _load_jsonl()
        traces = [done[q["id"]] for q in draw() if q["id"] in done]
    else:
        traces = collect(force=args.force, only=args.only, spacing=args.delay)

    if not traces:
        print("no traces yet")
        return

    incomplete = [(t["trace_id"], missing_fields(t)) for t in traces]
    incomplete = [(tid, gaps) for tid, gaps in incomplete if gaps]
    if incomplete:
        print("\nWARNING: incomplete traces")
        for tid, gaps in incomplete:
            print(f"  {tid}: missing {gaps}")

    JSON_PATH.write_text(json.dumps(traces, indent=2, ensure_ascii=False), encoding="utf-8")
    MD_PATH.write_text(render(traces), encoding="utf-8")

    counts: dict[str, int] = {}
    for t in traces:
        counts[t["grading"]["outcome"]] = counts.get(t["grading"]["outcome"], 0) + 1
    print()
    print(f"collected {len(traces)}/{W5_SAMPLE_SIZE}: " +
          ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print(f"wrote {MD_PATH}")
    print(f"wrote {JSON_PATH}")

    unsettled = [t["trace_id"] for t in traces if not _is_settled(t)]
    if unsettled:
        print()
        print(f"{len(unsettled)} trace(s) still errored: {', '.join(unsettled)}")
        print("Re-run this command later to retry only those.")


if __name__ == "__main__":
    main()
