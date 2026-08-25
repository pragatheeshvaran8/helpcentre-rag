"""Week 4 failure separation: which kind of wrong is each failure?

"Wrong sometimes" is useless to fix. There are two kinds of wrong and they need
completely different fixes:

    BUCKET A - wrong document fetched
        The answering chunk is not in the top-k. The model never saw the answer,
        so no amount of prompt work or model upgrade can help. A smarter model
        changes nothing here. Fix retrieval.

    BUCKET B - right document, wrong answer
        The answering chunk IS in the top-k, and the final answer is still wrong
        or refused. Retrieval did its job. Fix the prompt, the context layout,
        or the model.

HOW EACH BUCKET IS DECIDED, MECHANICALLY
    retrieval_ok
        One of the top-k chunks has the expected article_id and literally
        contains every must_contain string. Same rule as Week 3 and w4_measure,
        so the three files agree.

    answer_ok
        The model did not refuse, AND at least one chunk_id it cited resolves to
        a chunk that satisfies the same must_contain rule.

        This is checkable rather than a judgement call. Under the forced-citation
        prompt, an answer grounded in the right chunk is right by construction,
        and one citing a neighbouring table row is not. It also catches the
        nastiest case: a fluent answer citing the wrong row.

    label
        not retrieval_ok                  -> A, wrong document fetched
        retrieval_ok and not answer_ok    -> B, right document, wrong answer
        otherwise                         -> pass

Both retrieval modes are labelled, so the write-up can say which bucket the one
change emptied and which bucket it left untouched.

Run:  python -m evals.w4_failures
      python -m evals.w4_failures --mode dense     (label one mode only)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from config import MODES, STRATEGY_STRUCTURED, get_settings
from evals.w4_questions import W4_K, W4_QUESTIONS
from rag import term
from rag.answerer import answer_question
from rag.retriever import chunk_answers_question

BUCKET_A = "A: wrong document fetched"
BUCKET_B = "B: right document, wrong answer"
PASS = "pass"
ERROR = "error: generation call failed"

# Compact labels for the summary tables. Anything unknown renders as "err", so
# a run that lost calls to an API failure is never mistaken for a run of passes.
SHORT_LABEL = {PASS: "pass", BUCKET_A: "**A**", BUCKET_B: "**B**"}


def label_one(question: dict, mode: str, strategy: str) -> dict:
    """Answer one question and decide which bucket it falls in.

    A failed API call is recorded as ERROR rather than raised. Labelling 30
    questions in two modes is 60 paid calls, and losing all of them because the
    59th failed is not acceptable. An ERROR row is honestly distinguishable from
    a real bucket, so a partial run is still usable and is never mistaken for a
    pass.
    """
    try:
        ans = answer_question(
            question["question"], strategy, k=W4_K, mode=mode, use_gate=True
        )
    except Exception as exc:
        return {
            "question_id": question["id"],
            "code": question["code"],
            "question": question["question"],
            "mode": mode,
            "label": ERROR,
            "retrieval_ok": None,
            "answer_ok": None,
            "refused": None,
            "gate_fired": None,
            "answer": f"{type(exc).__name__}: {exc}",
            "answer_rank": None,
            "cited": [],
            "cited_resolve": False,
            "grounded_in": [],
            "fetched": [],
        }

    # Did retrieval put the answering chunk in front of the model?
    answering = [
        h
        for h in ans.retrieved
        if h["article_id"] == question["expected_article_id"]
        and chunk_answers_question(h["text"], question["must_contain"])
    ]
    retrieval_ok = bool(answering)

    # Did the model ground its answer in a chunk that really holds the answer?
    grounded = [
        c
        for c in ans.citations
        if c.resolves
        and c.article_id == question["expected_article_id"]
        and c.text
        and chunk_answers_question(c.text, question["must_contain"])
    ]
    answer_ok = (not ans.refused) and bool(grounded)

    if not retrieval_ok:
        label = BUCKET_A
    elif not answer_ok:
        label = BUCKET_B
    else:
        label = PASS

    return {
        "question_id": question["id"],
        "code": question["code"],
        "question": question["question"],
        "mode": mode,
        "label": label,
        "retrieval_ok": retrieval_ok,
        "answer_ok": answer_ok,
        "refused": ans.refused,
        "gate_fired": ans.gate_fired,
        "answer": ans.answer,
        "answer_rank": answering[0]["rank"] if answering else None,
        "cited": [c.chunk_id for c in ans.citations],
        "cited_resolve": all(c.resolves for c in ans.citations) if ans.citations else False,
        "grounded_in": [c.chunk_id for c in grounded],
        "fetched": [
            {
                "rank": h["rank"],
                "chunk_id": h["chunk_id"],
                "article_id": h["article_id"],
                "found_by": h.get("found_by"),
                "is_answer_chunk": h in answering,
            }
            for h in ans.retrieved
        ],
    }


def counts(records: list[dict], mode: str) -> dict:
    subset = [r for r in records if r["mode"] == mode]
    return {
        "mode": mode,
        "n": len(subset),
        "pass": sum(1 for r in subset if r["label"] == PASS),
        "bucket_a": sum(1 for r in subset if r["label"] == BUCKET_A),
        "bucket_b": sum(1 for r in subset if r["label"] == BUCKET_B),
        "errors": sum(1 for r in subset if r["label"] == ERROR),
        "a_ids": [r["question_id"] for r in subset if r["label"] == BUCKET_A],
        "b_ids": [r["question_id"] for r in subset if r["label"] == BUCKET_B],
    }


def write_failures(report: dict, path: Path) -> None:
    recs = report["records"]
    modes = report["modes"]
    k = report["k"]
    total_errors = sum(report["counts"][m].get("errors", 0) for m in modes)
    lines = [
        f"# Week 4 failure separation, at k={k}",
        "",
    ]
    if total_errors:
        lines += [
            f"> **INCOMPLETE RUN.** {total_errors} generation call(s) failed, so those",
            "> questions carry no label. They are shown as `err`, never as a pass.",
            "> Re-run `python -m evals.w4_failures` to fill them in. Labels that did",
            "> succeed are cached, so a rerun only pays for the missing ones.",
            "",
        ]
    lines += [
        "Two kinds of wrong, decided mechanically. See the module docstring in",
        "`evals/w4_failures.py` for the exact rule.",
        "",
        f"- **{BUCKET_A}** - the answering chunk was not in the top-{k}. "
        "A smarter model cannot help. Fix retrieval.",
        f"- **{BUCKET_B}** - the answering chunk WAS in the top-{k} and the answer "
        "is still wrong or refused. Fix the prompt or the model.",
        "",
        "## Bucket counts",
        "",
        "| mode | pass | A: wrong document | B: right document, wrong answer |",
        "|---|---|---|---|",
    ]
    for mode in modes:
        c = report["counts"][mode]
        lines.append(
            f"| {mode} | {c['pass']}/{c['n']} | {c['bucket_a']} | {c['bucket_b']} |"
        )

    lines += ["", "## Every question, labelled", "", "| Q | code |"]
    lines[-1] += "".join(f" {m} |" for m in modes)
    lines.append("|---|---|" + "---|" * len(modes))
    for q in W4_QUESTIONS:
        row = f"| {q['id']} | `{q['code']}` |"
        for mode in modes:
            r = next(
                x for x in recs if x["question_id"] == q["id"] and x["mode"] == mode
            )
            short = SHORT_LABEL.get(r["label"], "err")
            row += f" {short} |"
        lines.append(row)

    # Detailed evidence for anything that is not a pass, in any mode.
    failing_ids = sorted(
        {r["question_id"] for r in recs if r["label"] != PASS},
        key=lambda qid: int(qid[1:]),
    )
    lines += [
        "",
        "## Evidence for each failure",
        "",
        f"{len(failing_ids)} question(s) failed in at least one mode.",
        "",
    ]
    if not failing_ids:
        lines.append("_No failures in either mode._")
    for qid in failing_ids:
        q = next(x for x in W4_QUESTIONS if x["id"] == qid)
        lines += [
            "---",
            "",
            f"### {qid} - `{q['code']}`",
            "",
            f"**Question:** {q['question']}",
            "",
            f"**Answer lives in:** `{q['expected_article_id']}` -> {q['expected_section']}",
            "",
            "**Hit requires:** " + ", ".join(f"`{m}`" for m in q["must_contain"]),
            "",
        ]
        for mode in modes:
            r = next(x for x in recs if x["question_id"] == qid and x["mode"] == mode)
            lines += [
                f"#### {mode} -> {r['label']}",
                "",
                f"- retrieval put the answering chunk in top-{k}: "
                f"**{'yes' if r['retrieval_ok'] else 'no'}**",
                f"- model refused: **{'yes' if r['refused'] else 'no'}**"
                + (" (gate fired)" if r["gate_fired"] else ""),
                f"- answer grounded in a chunk that holds the answer: "
                f"**{'yes' if r['answer_ok'] else 'no'}**",
                "",
                "What was fetched:",
                "",
                "| rank | chunk_id | article | arm | holds the answer |",
                "|---|---|---|---|---|",
            ]
            for f in r["fetched"]:
                lines.append(
                    f"| {f['rank']} | `{f['chunk_id']}` | {f['article_id']} "
                    f"| {f['found_by'] or 'dense'} "
                    f"| {'**yes**' if f['is_answer_chunk'] else 'no'} |"
                )
            lines += [
                "",
                "Final answer:",
                "",
                "```",
                r["answer"],
                "```",
                "",
            ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_inspection(report: dict, path: Path) -> None:
    """The inspection view: question, what was fetched, and the final answer."""
    recs = report["records"]
    modes = report["modes"]
    lines = [
        "# Week 4 inspection view",
        "",
        "Question, what was fetched, and the final answer, side by side. This is",
        "the view that makes a failure diagnosable in one glance: if the fetched",
        "column has no answer chunk, the answer column was never going to be",
        "right.",
        "",
        "`>` marks the chunk that actually holds the answer.",
        "",
    ]
    for mode in modes:
        lines += [
            f"## Mode: {mode}",
            "",
            "| Q | question | fetched (top-3) | final answer | verdict |",
            "|---|---|---|---|---|",
        ]
        for q in W4_QUESTIONS:
            r = next(
                x for x in recs if x["question_id"] == q["id"] and x["mode"] == mode
            )
            fetched = "<br>".join(
                ("**&gt; " + f["chunk_id"] + "**") if f["is_answer_chunk"] else f["chunk_id"]
                for f in r["fetched"]
            )
            answer = r["answer"].replace("\n", " ").replace("|", "\\|")
            if len(answer) > 180:
                answer = answer[:180] + " ..."
            verdict = SHORT_LABEL.get(r["label"], "err")
            lines.append(
                f"| {q['id']} | {q['question'][:70]} | {fetched} | {answer} | {verdict} |"
            )
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def load_cache(path: Path) -> dict[tuple[str, str], dict]:
    """Reload successful labels from a previous run.

    Every label costs one paid API call, so a rerun must not pay twice for work
    already done. ERROR rows are deliberately not cached, so a run that died on
    a credit limit retries exactly the questions it never reached.
    """
    if not path.exists():
        return {}
    try:
        prior = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return {
        (r["question_id"], r["mode"]): r
        for r in prior.get("records", [])
        if r.get("label") and r["label"] != ERROR
    }


def main() -> None:
    term.init()
    parser = argparse.ArgumentParser(description="Label Week 4 failures by type.")
    parser.add_argument("--mode", choices=list(MODES), help="Label one mode only.")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Ignore cached labels and re-run every generation call.",
    )
    args = parser.parse_args()

    modes = [args.mode] if args.mode else list(MODES)
    settings = get_settings()
    out = Path(settings.results_dir)
    json_path = out / "w4_failures.json"

    cache = {} if args.refresh else load_cache(json_path)
    if cache:
        print(term.grey(f"Reusing {len(cache)} label(s) from a previous run."))

    records: list[dict] = []

    def checkpoint() -> None:
        """Persist after every question, so a crash never loses paid work."""
        json_path.write_text(
            json.dumps(
                {
                    "k": W4_K,
                    "strategy": STRATEGY_STRUCTURED,
                    "modes": modes,
                    "model": settings.openrouter_model,
                    "counts": {m: counts(records, m) for m in modes},
                    "records": records,
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    colours = {PASS: term.green, BUCKET_A: term.red, BUCKET_B: term.yellow}

    for mode in modes:
        print()
        print(term.bold(f"-- labelling {len(W4_QUESTIONS)} questions in {mode} mode"))
        for q in W4_QUESTIONS:
            cached = cache.get((q["id"], mode))
            r = cached or label_one(q, mode, STRATEGY_STRUCTURED)
            records.append(r)
            checkpoint()
            colour = colours.get(r["label"], term.magenta)
            note = term.grey("  (cached)") if cached else ""
            print(f"   {q['id']:<5}{q['code']:<11}{colour(r['label'])}{note}")

    report = {
        "k": W4_K,
        "strategy": STRATEGY_STRUCTURED,
        "modes": modes,
        "model": settings.openrouter_model,
        "counts": {mode: counts(records, mode) for mode in modes},
        "records": records,
    }

    write_failures(report, out / "w4_failures.md")
    write_inspection(report, out / "w4_inspect.md")
    checkpoint()

    print()
    print(term.bold(f"{'mode':<10}{'pass':<8}{'A: wrong doc':<16}{'B: wrong answer':<16}"))
    print("-" * 50)
    for mode in modes:
        c = report["counts"][mode]
        passed = f"{c['pass']}/{c['n']}"
        print(
            f"{mode:<10}{passed:<8}"
            f"{term.red(str(c['bucket_a'])):<16}{term.yellow(str(c['bucket_b'])):<16}"
        )
    print()
    print(f"Wrote {out / 'w4_failures.md'}")
    print(f"Wrote {out / 'w4_inspect.md'}")


if __name__ == "__main__":
    main()
