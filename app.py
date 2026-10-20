"""Tier-1 Deflection Assistant. The single entry point.

    python app.py doctor            is this machine ready?
    python app.py ask "ERR-4032?"   answer one ticket
    python app.py demo              the four-part demo
    python app.py eval              the full test suite
    python app.py logs --find ...   search past answers
    python app.py report            where every number came from

WHAT THIS APP IS FOR
    A support agent pastes a customer's ticket. The app answers it from the
    help centre, cites the exact paragraph it used, and refuses when the
    corpus does not hold the answer. The agent sends the reply or escalates.

    It is called a deflection assistant because its job is to settle tier-1
    tickets without a human reading the article. It only earns that name if a
    wrong answer is rare and a refusal is honest, which is what eleven weeks
    of measurement were for.

WHY THIS FILE EXISTS
    Until this week the project had eleven separate `run_*.py` commands, one
    per module, each its own front door. That is fine for a course and useless
    to anyone else: a stranger has no way to know which one to type.

    This is the one door. Everything else is still there, still runnable, and
    nothing here duplicates it: each subcommand calls the module that already
    does the work.

WHAT RUNS WHEN YOU ASK A QUESTION
    1. Start the MCP servers listed in mcp_servers.json and ask what tools
       they have. Nothing is hard-coded.                          (Week 9)
    2. Loop: pick a tool, run it, look at the result, pick again. Budgets stop
       it running away.                                            (Week 7)
    3. Retrieve with hybrid dense plus BM25 over structure-aware chunks.
                                                               (Weeks 3 and 4)
    4. Answer only from retrieved text, cite every sentence, refuse when the
       facts are missing.                                          (Week 6)
    5. Scan what came back and what goes out for injected instructions.
                                                                   (Week 8)
    6. Write a trace: the question, the answer, the chunks, and a span per
       step with its own time and cost.                           (Week 11)
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))


# ---------------------------------------------------------------------------
def cmd_doctor(args) -> int:
    """Is this machine ready? Run this first, and before any demo."""
    from rag import term

    term.init()
    print(term.rule("doctor"))
    problems: list[str] = []

    def line(label: str, ok: bool, detail: str = "", fix: str = "") -> None:
        """One check. `detail` is shown always, `fix` only when it failed."""
        mark = term.green("ok  ") if ok else term.red("FAIL")
        print(f"  {mark} {label:38} {term.grey(detail if ok else (fix or detail))}")
        if not ok:
            problems.append(label)

    line("python 3.10 or newer", sys.version_info >= (3, 10),
         ".".join(str(n) for n in sys.version_info[:3]),
         fix="this app needs 3.10 or newer")

    try:
        import chromadb  # noqa: F401
        import langchain_openai  # noqa: F401
        import mcp  # noqa: F401
        line("dependencies installed", True, "chromadb, langchain, mcp")
    except ImportError as exc:
        line("dependencies installed", False,
             fix=f"{exc}. Run: pip install -r requirements.txt")

    from config import STRATEGY_STRUCTURED, get_settings

    settings = get_settings()
    key = settings.openrouter_api_key or ""
    line("a .env file with an API key", bool(key),
         f"key ending {key[-4:]}" if key else "",
         fix="copy .env.example to .env, then paste your OpenRouter key")
    line("model chosen", bool(settings.openrouter_model), settings.openrouter_model,
         fix="set OPENROUTER_MODEL in .env")

    corpus = sorted((BASE / "corpus").glob("*.md"))
    line("corpus present", len(corpus) >= 6, f"{len(corpus)} articles",
         fix=f"expected 6 articles in corpus/, found {len(corpus)}")

    # The embedding model loads to answer this, and the loader prints a hub
    # warning and a progress bar to stderr. Both land mid-line and make a clean
    # check look broken, so stderr is held and only replayed if the check fails.
    import contextlib
    import io
    import os

    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    noise = io.StringIO()
    try:
        from rag.vector_store import count_chunks

        with contextlib.redirect_stderr(noise):
            n = count_chunks(STRATEGY_STRUCTURED)
        line("search index built", n > 0, f"{n} chunks",
             fix="the index is empty. Run: python app.py index")
    except Exception as exc:
        line("search index built", False, fix=f"{type(exc).__name__}. Run: python app.py index")
        print(term.grey(noise.getvalue().strip()[:400]))

    print()
    if problems:
        print(term.red(f"  {len(problems)} thing(s) need fixing before this will run."))
        return 1
    print(term.green("  Ready. Try: python app.py ask \"What is the fix for ERR-4032?\""))
    return 0


# ---------------------------------------------------------------------------
def cmd_index(args) -> int:
    """Build the search index. Needed once, and after any corpus change.

    Safe to re-run. Ingest only adds articles the index does not already hold,
    so a second run costs seconds and changes nothing.
    """
    from rag import ingest

    sys.argv = ["ingest"]
    ingest.main()
    return 0


# ---------------------------------------------------------------------------
def unchecked_marks(answer: str) -> list[str]:
    """Bracket marks in the answer that are NOT help-centre chunk ids.

    Found at the seam, on a real run. The answer ended:

        ...escalate to Billing Ops [SUP-2041][SUP-2114].

    Those are real past tickets, served by the ticket-history server. They are
    not hallucinations. The problem is that they are printed in exactly the
    same brackets as `[HC-4002-structured-004]`, so the reader cannot tell a
    help-centre rule from one thing that happened to somebody once.

    The citation check never looked at them either. It matches only the
    HC-xxxx-strategy-nnn shape, so a `[SUP-2041]` is not an unresolved citation
    to it. It is nothing at all, and nothing is what got reported.

    This does not strip them. A past ticket is often the most useful line in
    the reply. It labels them, so the person sending it knows which half of the
    answer the help centre stands behind.
    """
    import re

    from rag.answerer import CITATION_RE

    chunk_ids = set(CITATION_RE.findall(answer or ""))
    marks = re.findall(r"\[([A-Za-z][A-Za-z0-9._-]{2,40})\]", answer or "")
    return list(dict.fromkeys(m for m in marks if m not in chunk_ids))


def cmd_ask(args) -> int:
    """Answer one ticket. This is the product."""
    from agent.budget import Budget
    from agent.loop import run as run_agent
    from rag import term

    term.init()
    question = " ".join(args.question).strip()
    if not question:
        print(term.red("Give me a ticket. Example:"))
        print('  python app.py ask "Customer hit ERR-4032 on an invoice. What do I do?"')
        return 2

    import textwrap

    print(term.rule("ticket"))
    for line in textwrap.wrap(question, 72):
        print(f"  {line}")
    print()

    # Load the corpus index before the agent starts, with stderr held. The
    # loader takes 13 to 40 seconds and prints a hub warning and a progress
    # bar, which otherwise land in the middle of the agent's step lines and
    # read as a crash. The captured text is replayed only if the load fails.
    from demo import _warm_the_index

    _warm_the_index()

    result = run_agent(
        question,
        budget=Budget(max_steps=args.max_steps, max_seconds=args.timeout),
        verbose=args.verbose,
    )

    print()
    print(term.rule("answer"))
    # The model returns one long paragraph per point. Wrapping is done here
    # rather than asking the prompt for short lines, because the prompt's job
    # is grounding and a terminal width is not its business.
    for para in (result.answer or "").split("\n"):
        if not para.strip():
            print()
            continue
        for line in textwrap.wrap(" ".join(para.split()), 72):
            print(f"  {line}")
    print()
    cited = [c.chunk_id for c in result.citations if c.resolves]
    unresolved = [c.chunk_id for c in result.citations if not c.resolves]
    other = unchecked_marks(result.answer or "")

    print(term.grey(f"  trace {result.trace_id}   {len(result.steps)} step(s)   "
                    f"{result.llm_calls} call(s)   {result.elapsed_s}s"))
    print(term.grey(f"  help centre: {', '.join(cited) if cited else 'nothing cited'}"))
    if unresolved:
        print(term.red(f"  NOT A REAL CHUNK: {', '.join(unresolved)}. Do not send this."))
    if other:
        print(term.yellow(f"  not help centre: {', '.join(other)}"))
        print(term.yellow("  Those are past tickets, not policy. One ticket is not a rule."))
        print(term.yellow("  Check anything they support before you send it."))
    if result.refused:
        print(term.yellow("  This was a refusal. The corpus does not hold the answer."))
    if result.injection_hits:
        print(term.yellow(f"  Guard stripped {len(result.injection_hits)} instruction-like "
                          "passage(s) from retrieved text."))
    print()
    print(term.grey("  Quote that trace id to look this answer up later:"))
    print(term.grey(f"    python app.py logs --trace {result.trace_id}"))
    return 0


# ---------------------------------------------------------------------------
def cmd_logs(args) -> int:
    """Find a past answer. The support drill, as a command."""
    from obs import search, store
    from rag import term

    term.init()
    if args.trace:
        row = store.by_id(args.trace)
        if row is None:
            print(term.red(f"No trace {args.trace!r}."))
            return 1
        print(term.rule(f"trace {row['trace_id']}"))
        print(f"  when     {row['at']}")
        print(f"  asked    {' '.join(row['question'].split())}")
        print(f"  answered {' '.join((row['answer'] or '').split())[:200]}")
        print(f"  cited    {', '.join(row.get('citations') or []) or 'nothing'}")
        print()
        print(f"  {'step':34} {'ms':>9} {'in':>7} {'out':>6} {'cost':>11}")
        for sp in row.get("spans") or []:
            print(f"  {sp['name'][:34]:34} {sp['ms']:>9} {sp['input_tokens']:>7} "
                  f"{sp['output_tokens']:>6} {sp['cost']:>11.8f}")
        print(f"  {'TOTAL':34} {row['ms']:>9} {row['input_tokens']:>7} "
              f"{row['output_tokens']:>6} {row['cost']:>11.8f}")
        return 0

    if args.suspicious:
        print(term.rule("answers worth a second look"))
        hits = search.suspicious()
        for h in hits[:args.limit]:
            print(f"  {h.trace_id}  {h.trace['at'][:19]}  {term.yellow(h.why)}")
            print(f"      {' '.join(h.trace['question'].split())[:80]}")
        if not hits:
            print(term.green("  Nothing flagged."))
        return 0

    complaint = " ".join(args.find or []).strip()
    hits, report = search.search(complaint, since=args.since, until=args.until,
                                limit=args.limit)
    print(term.rule("search"))
    for label, n in report["funnel"]:
        print(f"  {label:44} -> {n}")
    print()
    print(f"  {len(hits)} hit(s) in {report['ms']}ms over {report['searched']} traces")
    for h in hits:
        print(f"  {h.line()}")
    return 0


# ---------------------------------------------------------------------------
def cmd_eval(args) -> int:
    """The full test suite. No API key needed."""
    import subprocess

    return subprocess.call([sys.executable, str(BASE / "test_acceptance.py")]
                           + (["--with-generation"] if args.with_generation else []))


# ---------------------------------------------------------------------------
def cmd_report(args) -> int:
    """Where every number came from. One line per week."""
    from rag import term

    term.init()
    print(term.rule("where the numbers come from"))
    rows = [
        ("3", "chunking", "structure-aware beats fixed-size", "results/results.md"),
        ("4", "retrieval", "hybrid: hit-rate@3 0.75 -> 0.95", "results/w4_results.md"),
        ("5", "error analysis", "20 traces read by hand", "results/w5_results.md"),
        ("6", "evaluation", "prompt v1 -> v2: 46.5% -> 79.1%", "results/w6_results.md"),
        ("7", "agents", "agent 12/12 vs fixed workflow 8/12", "results/w7_results.md"),
        ("8", "failure modes", "outcome 12/12, path 10/12", "results/w8_results.md"),
        ("9", "MCP", "a server bolted on, 0 agent bytes changed", "results/w9_results.md"),
        ("10", "multi-agent", "single 11/12 vs squad 10/12", "results/w10_results.md"),
        ("11", "production", "cost/request -76%, 0 wrong answers", "results/w11_results.md"),
        ("12", "capstone", "one entry point; 2 seam bugs found", "results/w12_results.md"),
    ]
    print(f"  {'wk':3} {'topic':16} {'the number':42} where")
    for wk, topic, number, where in rows:
        exists = (BASE / where).exists()
        mark = "" if exists else term.red("  (missing)")
        print(f"  {wk:3} {topic:16} {number:42} {where}{mark}")
    print()
    print(term.grey("  Every one of those is reproducible. The command is in its own file."))
    return 0


# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    """The whole command surface, in one place so a test can read it."""
    parser = argparse.ArgumentParser(
        prog="app.py",
        description="Tier-1 Deflection Assistant: answer a support ticket from the help centre.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "start here:\n"
            "  python app.py doctor\n"
            '  python app.py ask "What is the fix for ERR-4032?"\n'
            "  python app.py demo\n"
        ),
    )
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("doctor", help="Check this machine is ready.")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("index", help="Build the search index.")
    p.set_defaults(func=cmd_index)

    p = sub.add_parser("ask", help="Answer one support ticket.")
    p.add_argument("question", nargs="+")
    p.add_argument("--max-steps", type=int, default=6)
    p.add_argument("--timeout", type=float, default=900.0)
    p.add_argument("-v", "--verbose", action="store_true", help="Show each step.")
    p.set_defaults(func=cmd_ask)

    p = sub.add_parser("demo", help="The four-part demo.")
    p.add_argument("--live", action="store_true",
                   help="Ask a real question instead of replaying a logged one.")
    p.set_defaults(func=lambda a: __import__("demo", fromlist=["run"]).run(live=a.live))

    p = sub.add_parser("eval", help="Run the full test suite.")
    p.add_argument("--with-generation", action="store_true")
    p.set_defaults(func=cmd_eval)

    p = sub.add_parser("logs", help="Find a past answer.")
    p.add_argument("--trace", help="Look one up by id.")
    p.add_argument("--find", nargs="+", help="Words from the complaint.")
    p.add_argument("--since", help="ISO date.")
    p.add_argument("--until", help="ISO date.")
    p.add_argument("--suspicious", action="store_true", help="Answers worth a second look.")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=cmd_logs)

    p = sub.add_parser("report", help="Where every number came from.")
    p.set_defaults(func=cmd_report)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    return args.func(args) or 0


if __name__ == "__main__":
    raise SystemExit(main())
