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
    :area api             filter to a product_area
    :area off             clear the filter
    :k 3                  change how many chunks are retrieved
    :search on|off        toggle generation off to see retrieval only
    :quit                 leave
"""
from __future__ import annotations

import argparse
import sys

from config import STRATEGIES, STRATEGY_STRUCTURED, get_settings

PRODUCT_AREAS = ("billing_core", "invoicing", "payments", "subscriptions", "tax", "api")


class Session:
    """Mutable settings for one terminal session."""

    def __init__(self, strategy: str, k: int, search_only: bool) -> None:
        self.strategy = strategy
        self.k = k
        self.search_only = search_only
        self.product_area: str | None = None

    def banner(self) -> str:
        area = self.product_area or "off"
        mode = "search-only" if self.search_only else "search + answer"
        return f"[{self.strategy}  k={self.k}  area={area}  {mode}]"


def show_hits(hits: list[dict]) -> None:
    if not hits:
        print("  nothing retrieved.")
        return
    for h in hits:
        flags = []
        if h["orphan_table_rows"]:
            flags.append("HEADER-LESS TABLE")
        elif h["has_table_header"]:
            flags.append("table+header")
        flag = ("  <- " + ", ".join(flags)) if flags else ""
        print(
            f"\n  {h['rank']}. score {h['score']:.4f}  {h['chunk_id']}"
            f"  [{h['article_id']} / {h['product_area']} / {h['last_updated']}]{flag}"
        )
        body = h["text"].strip()
        preview = body if len(body) <= 400 else body[:400] + " ..."
        for line in preview.splitlines():
            print(f"     {line}")


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
        else:
            print(f"  strategy must be one of {list(STRATEGIES)}")
    elif cmd == ":area":
        if arg in ("off", "none", ""):
            session.product_area = None
        elif arg in PRODUCT_AREAS:
            session.product_area = arg
        else:
            print(f"  area must be 'off' or one of {list(PRODUCT_AREAS)}")
    elif cmd == ":k":
        if arg.isdigit() and int(arg) > 0:
            session.k = int(arg)
        else:
            print("  k must be a positive integer")
    elif cmd == ":search":
        session.search_only = arg != "off"
    else:
        print(f"  unknown command {cmd}. Try :help")
    return True


def ask(question: str, session: Session) -> None:
    from rag.retriever import format_hits, search

    if session.search_only:
        hits = format_hits(
            search(question, session.strategy, k=session.k, product_area=session.product_area)
        )
        print(f"\nRetrieved {len(hits)} chunk(s):")
        show_hits(hits)
        return

    from rag.answerer import answer_question

    result = answer_question(
        question,
        session.strategy,
        k=session.k,
        product_area=session.product_area,
        use_gate=True,
    )

    print()
    if result.refused:
        where = "relevance gate" if result.gate_fired else "the model"
        print(f"--- REFUSED by {where} ---")
    else:
        print("--- ANSWER ---")
    print(result.answer)

    if result.citations:
        print("\n--- CITATION CHECK ---")
        for c in result.citations:
            state = "resolves" if c.resolves else "DOES NOT RESOLVE"
            seen = "" if c.was_in_context else "  (NOT IN CONTEXT)"
            print(f"  {c.chunk_id}: {state}, {c.source_file or '-'}{seen}")
    elif not result.refused:
        print("\n--- CITATION CHECK ---\n  no citations produced")

    print("\n--- WHAT RETRIEVAL RETURNED ---")
    show_hits(result.retrieved)


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Ask the help-centre index a question.")
    parser.add_argument("question", nargs="*", help="Ask one question and exit.")
    parser.add_argument(
        "--strategy", default=STRATEGY_STRUCTURED, choices=list(STRATEGIES)
    )
    parser.add_argument("--k", type=int, default=settings.top_k)
    parser.add_argument("--area", default=None, help="Filter to a product_area.")
    parser.add_argument(
        "--search-only",
        action="store_true",
        help="Retrieval only. No LLM call, no API key needed.",
    )
    args = parser.parse_args()

    session = Session(args.strategy, args.k, args.search_only)
    session.product_area = args.area

    print("Loading the embedding model. This takes about 25 seconds the first time.")
    from rag.vector_store import count_chunks

    counts = {s: count_chunks(s) for s in STRATEGIES}
    if not any(counts.values()):
        print("\nThe index is empty. Build it first:\n\n    python -m rag.ingest\n")
        raise SystemExit(1)
    print(f"Index ready: " + ", ".join(f"{s}={n} chunks" for s, n in counts.items()))

    if args.question:
        ask(" ".join(args.question), session)
        return

    print("\nType a question, or :help for commands, or :quit to leave.")
    while True:
        try:
            raw = input(f"\n{session.banner()}\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not raw:
            continue
        if raw.startswith(":"):
            if not handle_command(raw, session):
                break
            continue
        try:
            ask(raw, session)
        except Exception as exc:  # keep the session alive on a bad call
            print(f"\n  failed: {exc}")

    print("Bye.")


if __name__ == "__main__":
    main()
