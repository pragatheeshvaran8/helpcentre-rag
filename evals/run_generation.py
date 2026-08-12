"""Requirement 5: 3 cited answers and 3 forced refusals.

CITED ANSWERS
    Three questions the corpus can answer. Every sentence must carry a
    [chunk_id]. After generation, every cited id is resolved against the live
    vector store and the chunk text is printed in full, so a grader can check
    that the cited chunk really contains the claim.

REFUSALS
    Three questions the corpus cannot answer. The retrieval gate is DISABLED for
    these on purpose, so the model is shown real retrieved context and must
    refuse anyway. A refusal produced by a code path that never called the model
    would prove nothing about the grounding prompt.

Run:  python -m evals.run_generation
"""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from config import STRATEGY_STRUCTURED, get_settings
from evals.questions import ANSWERABLE, OUT_OF_CORPUS, get_question
from rag.answerer import SYSTEM_PROMPT, Answer, answer_question


def _citation_section(ans: Answer) -> list[str]:
    if not ans.citations:
        return ["_No citations were produced._", ""]
    lines = [
        "| chunk_id | resolves in store | was in context | article | source_file |",
        "|---|---|---|---|---|",
    ]
    for c in ans.citations:
        lines.append(
            f"| [`{c.chunk_id}`](chunks_structured.md#{c.chunk_id.lower()}) "
            f"| {'yes' if c.resolves else 'NO'} "
            f"| {'yes' if c.was_in_context else 'NO'} "
            f"| {c.article_id or '-'} | {c.source_file or '-'} |"
        )
    lines.append("")
    lines.append("Full text of every cited chunk, read back from the vector store:")
    lines.append("")
    for c in ans.citations:
        lines += [f"<a id=\"{c.chunk_id.lower()}\"></a>", f"**`{c.chunk_id}`**", "", "```"]
        lines.append(c.text if c.text else "!! DOES NOT RESOLVE - FABRICATED CITATION !!")
        lines += ["```", ""]
    return lines


def _retrieval_table(ans: Answer) -> list[str]:
    lines = [
        "| rank | score | chunk_id | article | product_area |",
        "|---|---|---|---|---|",
    ]
    for h in ans.retrieved:
        lines.append(
            f"| {h['rank']} | {h['score']:.4f} | `{h['chunk_id']}` "
            f"| {h['article_id']} | {h['product_area']} |"
        )
    lines.append("")
    return lines


def run_cited(strategy: str) -> list[Answer]:
    out: list[Answer] = []
    for qid in ANSWERABLE:
        q = get_question(qid)
        print(f"  generating {qid} ...")
        out.append(answer_question(q["question"], strategy, use_gate=True))
    return out


def run_refusals(strategy: str) -> list[Answer]:
    out: list[Answer] = []
    for item in OUT_OF_CORPUS:
        print(f"  generating {item['id']} (gate disabled) ...")
        out.append(answer_question(item["question"], strategy, use_gate=False))
    return out


def write_report(cited: list[Answer], refusals: list[Answer], path: Path) -> None:
    settings = get_settings()
    lines = [
        "# Generation: 3 cited answers, 3 forced refusals",
        "",
        f"- Strategy searched: `{STRATEGY_STRUCTURED}`",
        f"- Model: `{settings.openrouter_model}` via OpenRouter, temperature "
        f"{settings.llm_temperature}",
        f"- Relevance gate: {settings.score_threshold} "
        "(ON for the cited answers, OFF for the refusals)",
        "",
        "## The grounding prompt, verbatim",
        "",
        "The refusal is an instruction with a fixed output string. The prompt",
        "never says \"use your best judgement\" and never says \"do your best\".",
        "",
        "```",
        SYSTEM_PROMPT,
        "```",
        "",
        "---",
        "",
        "# Part A - 3 answerable questions, cited",
        "",
    ]

    for qid, ans in zip(ANSWERABLE, cited):
        q = get_question(qid)
        resolved = "all citations resolve" if ans.all_citations_resolve else "CITATION FAILURE"
        lines += [
            f"## {qid}",
            "",
            f"**Question:** {ans.question}",
            "",
            f"**Known-correct location:** `{q['expected_article_id']}` -> {q['expected_section']}",
            "",
            "**Answer, verbatim:**",
            "",
            "```",
            ans.answer,
            "```",
            "",
            f"**Citation check: {resolved}** "
            f"({len(ans.citations)} distinct chunk_id(s) cited)",
            "",
            *_citation_section(ans),
            "**What retrieval returned:**",
            "",
            *_retrieval_table(ans),
            "---",
            "",
        ]

    lines += [
        "# Part B - 3 out-of-corpus questions, refused",
        "",
        "The gate is disabled for these three. Each model call was given the",
        "retrieved context shown below and still had to refuse. The retrieval",
        "scores prove the corpus had something topically close to offer.",
        "",
    ]

    for item, ans in zip(OUT_OF_CORPUS, refusals):
        verdict = "REFUSED" if ans.refused else "DID NOT REFUSE - FAILURE"
        lines += [
            f"## {item['id']}",
            "",
            f"**Question:** {ans.question}",
            "",
            f"**Why the corpus cannot answer it:** {item['why_unanswerable']}",
            "",
            f"**Verdict: {verdict}** (gate fired: {ans.gate_fired})",
            "",
            "**Model output, verbatim:**",
            "",
            "```",
            ans.answer,
            "```",
            "",
            "**Context the model was given before refusing:**",
            "",
            *_retrieval_table(ans),
            "<details><summary>Full context blocks sent to the model</summary>",
            "",
            "```",
            ans.context,
            "```",
            "",
            "</details>",
            "",
            "---",
            "",
        ]

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    settings = get_settings()
    out = Path(settings.results_dir)

    print("Cited answers:")
    cited = run_cited(STRATEGY_STRUCTURED)
    print("Refusals:")
    refusals = run_refusals(STRATEGY_STRUCTURED)

    write_report(cited, refusals, out / "generation.md")
    (out / "generation.json").write_text(
        json.dumps(
            {
                "cited": [asdict(a) for a in cited],
                "refusals": [asdict(a) for a in refusals],
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("--- cited answers ---")
    for qid, a in zip(ANSWERABLE, cited):
        bad = [c.chunk_id for c in a.citations if not c.resolves]
        print(
            f"  {qid}: refused={a.refused}  citations={len(a.citations)}  "
            f"all_resolve={a.all_citations_resolve}  unresolved={bad or 'none'}"
        )
    print("--- refusals ---")
    for item, a in zip(OUT_OF_CORPUS, refusals):
        print(
            f"  {item['id']}: refused={a.refused}  gate_fired={a.gate_fired}  "
            f"best_score={a.retrieved[0]['score'] if a.retrieved else 0:.4f}"
        )
    print()
    print(f"Wrote {out / 'generation.md'}")


if __name__ == "__main__":
    main()
