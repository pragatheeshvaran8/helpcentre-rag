"""Interactive terminal client for the help-centre index.

The evaluation scripts run a fixed set of questions and write files. This is the
other thing you want in a terminal: type your own question, see what retrieval
actually returned, and see whether the model answers it or refuses.

    python ask.py                     interactive, with grounded generation
    python ask.py --search-only       retrieval only, no LLM, no API key needed
    python ask.py "what is ERR-4032"  answer one question and exit

Inside the session:

    :help                 show commands
    :strategy structured  switch index (structured | baseline)
    :mode hybrid          switch retrieval (hybrid | dense)
    :area api             filter to a product_area
    :area off             clear the filter
    :k 3                  change how many chunks are retrieved
    :search on|off        toggle generation off to see retrieval only
    :quit                 leave

Output is colour-coded. The chunk the answer actually came from is marked
USED IN ANSWER, so you can tell at a glance which of the retrieved results
produced what you are reading.
"""
from __future__ import annotations

import argparse
import re

from config import MODES, STRATEGIES, STRATEGY_STRUCTURED, get_settings
from rag import term

PRODUCT_AREAS = ("billing_core", "invoicing", "payments", "subscriptions", "tax", "api")

PREVIEW_CHARS = 320


class Session:
    """Mutable settings for one terminal session."""

    def __init__(self, strategy: str, k: int, search_only: bool, mode: str) -> None:
        self.strategy = strategy
        self.k = k
        self.search_only = search_only
        self.mode = mode
        self.product_area: str | None = None

    def banner(self) -> str:
        area = self.product_area or "off"
        what = "search only" if self.search_only else "search + answer"
        return term.grey(
            f"[index={self.strategy}  retrieval={self.mode}  k={self.k}  "
            f"area={area}  {what}]"
        )


# ---------------------------------------------------------------------------
# Input guarding
# ---------------------------------------------------------------------------
# Lines that are obviously this program's own output rather than a question.
# A multi-line paste is delivered to input() one line at a time, so pasting a
# previous result back into the prompt fires one query per line. Left
# unguarded that floods the screen and burns an API call on every line.
# Fragments that only ever appear in this program's own rendered output.
_OUTPUT_MARKERS = (
    "<<< used in answer",
    "[table+header]",
    "[header-less table]",
    "[bm25 only]",
    "[dense only]",
    "rrf 0.0",
    "showing retrieval only",
    "resets at ",
    "== retrieval",
    "== answer",
    "== citation check",
    "== refused",
    "== no generation",
    "ok  resolves",
    "fail  does not resolve",
    "was not in the context",
)

# A result line: "  3. 0.7182  HC-..." or "  1. rrf 0.0328 [dense #1 ...]".
# Written without backslash escapes on purpose; an earlier version of this
# guard was silently broken by one that the source-level string ate.
_RESULT_LINE = re.compile("^[ 	]*[0-9]+[.][ 	]")


def looks_like_pasted_output(raw: str) -> bool:
    """Is this line our own output pasted back, rather than a question?

    A multi-line paste reaches input() one line at a time, so pasting a
    previous result into the prompt fires one query per line. Unguarded, that
    floods the screen and spends an API call on every line of it.
    """
    text = raw.strip()
    if not text or text.startswith(":"):
        return False
    # A markdown table row or heading from a chunk preview.
    if text.startswith("|") or text.startswith("#"):
        return True
    # A horizontal rule or a table separator, e.g. "|---|---|" or "=====".
    if set(text) <= set("-=| "):
        return True
    if _RESULT_LINE.match(text):
        return True
    low = text.lower()
    return any(marker in low for marker in _OUTPUT_MARKERS)


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------
def highlight_citations(text: str) -> str:
    """Make every [chunk_id] inside the answer stand out."""
    if not term.enabled():
        return text
    from rag.answerer import CITATION_RE

    return CITATION_RE.sub(lambda m: term.paint(m.group(0), "cyan", "bold"), text)


def show_hits(hits: list[dict], cited: set[str] | None = None) -> None:
    """Print the retrieved chunks, marking any that the answer actually used."""
    cited = cited or set()
    if not hits:
        print(term.grey("  nothing retrieved."))
        return

    for h in hits:
        used = h["chunk_id"] in cited

        if h["orphan_table_rows"]:
            tag = term.paint(" [HEADER-LESS TABLE]", "red", "bold")
        elif h["has_table_header"]:
            tag = term.green(" [table+header]")
        else:
            tag = term.grey(" [prose]")

        arm = h.get("found_by")
        if arm == "keyword only":
            tag += term.paint(" [BM25 ONLY]", "magenta", "bold")
        elif arm == "dense only":
            tag += term.grey(" [dense only]")

        marker = term.paint(" <<< USED IN ANSWER", "green", "bold") if used else ""
        chunk_id = (
            term.paint(h["chunk_id"], "green", "bold") if used else term.cyan(h["chunk_id"])
        )
        rank = term.bold(f"{h['rank']}.") if used else f"{h['rank']}."
        where = term.grey(f"{h['article_id']} / {h['product_area']}")

        # In hybrid mode the score is an RRF score, around 0.03, and on its
        # own it tells a reader nothing. What matters is WHERE each arm put
        # this chunk, so show the component ranks instead of a bare number.
        if "dense_rank" in h or "keyword_rank" in h:
            score = term.yellow(f"rrf {h['score']:.4f}")
            arms = term.grey(
                f"[dense #{h.get('dense_rank') or '-'}  bm25 #{h.get('keyword_rank') or '-'}]"
            )
            head = f"  {rank} {score} {arms}  {chunk_id}  {where}{tag}{marker}"
        else:
            score = term.yellow(f"{h['score']:.4f}")
            head = f"  {rank} {score}  {chunk_id}  {where}{tag}{marker}"
        print()
        print(head)

        body = h["text"].strip()
        preview = body if len(body) <= PREVIEW_CHARS else body[:PREVIEW_CHARS] + " ..."
        for line in preview.splitlines():
            print(term.grey(f"     {line}"))


def show_citations(citations: list) -> None:
    print()
    print(term.rule("CITATION CHECK", "cyan"))
    if not citations:
        print(term.yellow("  no citations produced"))
        return
    for c in citations:
        if c.resolves:
            state = term.green("OK  resolves")
        else:
            state = term.paint("FAIL  does not resolve", "red", "bold")
        warn = "" if c.was_in_context else term.red("  (was NOT in the context!)")
        print(f"  {state}  {term.cyan(c.chunk_id)}  {term.grey(c.source_file or '-')}{warn}")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
def handle_command(raw: str, session: Session) -> bool:
    """Run a ':' command. Returns False when the session should end."""
    parts = raw.split()
    cmd = parts[0].lower()
    arg = parts[1].lower() if len(parts) > 1 else ""

    if cmd in (":quit", ":q", ":exit"):
        return False

    if cmd == ":help":
        print(__doc__)
    elif cmd == ":strategy":
        if arg in STRATEGIES:
            session.strategy = arg
            print(term.green(f"  index -> {arg}"))
        else:
            print(term.red(f"  strategy must be one of {list(STRATEGIES)}"))
    elif cmd == ":mode":
        if arg in MODES:
            session.mode = arg
            print(term.green(f"  retrieval -> {arg}"))
        else:
            print(term.red(f"  mode must be one of {list(MODES)}"))
    elif cmd == ":area":
        if arg in ("off", "none", ""):
            session.product_area = None
            print(term.green("  filter cleared"))
        elif arg in PRODUCT_AREAS:
            session.product_area = arg
            print(term.green(f"  filter -> product_area={arg}"))
        else:
            print(term.red(f"  area must be 'off' or one of {list(PRODUCT_AREAS)}"))
    elif cmd == ":k":
        if arg.isdigit() and int(arg) > 0:
            session.k = int(arg)
            print(term.green(f"  k -> {arg}"))
        else:
            print(term.red("  k must be a positive integer"))
    elif cmd == ":search":
        session.search_only = arg != "off"
        print(term.green(f"  search only -> {session.search_only}"))
    else:
        print(term.red(f"  unknown command {cmd}. Try :help"))
    return True


# ---------------------------------------------------------------------------
# Asking
# ---------------------------------------------------------------------------
def ask(question: str, session: Session) -> None:
    from rag.hybrid import search_by_mode
    from rag.retriever import format_hits

    if session.search_only:
        hits = format_hits(
            search_by_mode(
                question,
                session.strategy,
                mode=session.mode,
                k=session.k,
                product_area=session.product_area,
            )
        )
        print()
        print(term.rule(f"RETRIEVAL  top {len(hits)}", "blue"))
        show_hits(hits)
        return

    from rag.answerer import (
        _is_generation_unavailable,
        _is_rate_limit_error,
        _rate_limit_reset,
        answer_question,
    )

    try:
        result = answer_question(
            question,
            session.strategy,
            k=session.k,
            product_area=session.product_area,
            use_gate=True,
            mode=session.mode,
        )
    except Exception as exc:
        if not _is_generation_unavailable(exc):
            raise
        # The provider will not answer, for quota reasons. Retrieval costs
        # nothing and still answers the question, so show that rather than a
        # provider stack trace. The answer is in the chunk text; the model was
        # only going to summarise it.
        print()
        if _is_rate_limit_error(exc):
            print(term.rule("NO GENERATION - DAILY REQUEST LIMIT REACHED", "red"))
            print(term.yellow("  The free-model daily request quota is spent."))
            reset = _rate_limit_reset(exc)
            if reset:
                print(term.yellow(f"  Resets at {reset}."))
            print(term.grey("  Waiting is the only fix. A smaller request will not help."))
        else:
            print(term.rule("NO GENERATION - OUT OF API CREDIT", "red"))
            print(term.yellow("  The provider refused even a single context block."))
        print(term.grey("  Showing retrieval only. The answer is in the text below."))
        print(term.grey("  Use ':search on' to skip generation without the failed call."))
        hits = format_hits(
            search_by_mode(
                question,
                session.strategy,
                mode=session.mode,
                k=session.k,
                product_area=session.product_area,
            )
        )
        print()
        print(term.rule(f"RETRIEVAL  top {len(hits)}", "blue"))
        show_hits(hits)
        return

    print()
    if getattr(result, "budget_degraded", False):
        print(
            term.yellow(
                f"  NOTE: low API credit. Answered on {len(result.retrieved)} "
                f"context block(s) instead of {session.k}."
            )
        )
    if result.refused:
        who = "the relevance gate" if result.gate_fired else "the model"
        print(term.rule(f"REFUSED by {who}", "red"))
        print(term.yellow(result.answer))
    else:
        print(term.rule("ANSWER", "green"))
        print(highlight_citations(result.answer))

    if result.citations or not result.refused:
        show_citations(result.citations)

    cited = {c.chunk_id for c in result.citations}
    print()
    print(term.rule(f"RETRIEVAL  top {len(result.retrieved)}", "blue"))
    show_hits(result.retrieved, cited=cited)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Ask the help-centre index a question.")
    parser.add_argument("question", nargs="*", help="Ask one question and exit.")
    parser.add_argument("--strategy", default=STRATEGY_STRUCTURED, choices=list(STRATEGIES))
    parser.add_argument(
        "--mode",
        default=None,
        choices=list(MODES),
        help="Retrieval mode. Defaults to settings.retrieval_mode.",
    )
    parser.add_argument("--k", type=int, default=settings.top_k)
    parser.add_argument("--area", default=None, help="Filter to a product_area.")
    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Retrieval only. No LLM call, no API key needed.",
    )
    parser.add_argument("--no-color", action="store_true", help="Disable colour output.")
    parser.add_argument("--color", action="store_true", help="Force colour output.")
    args = parser.parse_args()

    term.init(False if args.no_color else (True if args.color else None))

    session = Session(
        args.strategy, args.k, args.search_only, args.mode or settings.retrieval_mode
    )
    session.product_area = args.area

    print(term.grey("Loading the embedding model. About 25 seconds the first time."))
    from rag.vector_store import count_chunks

    counts = {s: count_chunks(s) for s in STRATEGIES}
    if not any(counts.values()):
        print(term.red("\nThe index is empty. Build it first:\n\n    python -m rag.ingest\n"))
        raise SystemExit(1)
    ready = ", ".join(f"{s}={n}" for s, n in counts.items())
    print(term.green(f"Index ready ({ready} chunks)."))

    if args.question:
        ask(" ".join(args.question), session)
        return

    print(term.grey("\nType a question, :help for commands, :quit to leave."))
    while True:
        try:
            raw = input(f"\n{session.banner()}\n{term.paint('>', 'magenta', 'bold')} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not raw:
            continue
        if looks_like_pasted_output(raw):
            # Almost certainly a pasted result, not a question. Skip it in
            # silence apart from one short note, so a large accidental paste
            # scrolls past harmlessly instead of firing a query per line.
            skipped += 1
            if skipped == 1:
                print(term.grey("  (ignoring pasted output. Ctrl+C to clear the queue.)"))
            continue
        skipped = 0
        if raw.startswith(":"):
            if not handle_command(raw, session):
                break
            continue
        try:
            ask(raw, session)
        except Exception as exc:  # keep the session alive on a bad call
            print(term.red(f"\n  failed: {exc}"))

    print(term.grey("Bye."))


if __name__ == "__main__":
    main()
