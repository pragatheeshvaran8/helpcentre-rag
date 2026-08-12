"""Run the whole pipeline in ONE process.

Each stage can be run on its own, but every separate process pays the cost of
loading torch and the embedding model again, which dominates the wall clock.
This runner loads the model once and reuses it for every stage.

Run:  python -m evals.run_all
      python -m evals.run_all --skip-generation      # no API key needed
"""
from __future__ import annotations

import argparse
import time


def main() -> None:
    parser = argparse.ArgumentParser(description="Run ingest and every evaluation.")
    parser.add_argument(
        "--skip-ingest", action="store_true", help="Reuse the existing index."
    )
    parser.add_argument(
        "--skip-generation",
        action="store_true",
        help="Skip the stages that call the LLM (no API key needed).",
    )
    args = parser.parse_args()

    from rag import ingest
    from evals import dump_chunks, run_bonus, run_filter_demo, run_generation, run_search_eval

    stages: list[tuple[str, callable]] = []
    if not args.skip_ingest:
        stages.append(("ingest", ingest.main))
    stages += [
        ("search evaluation", run_search_eval.main),
        ("filter demo", run_filter_demo.main),
        ("chunk dump", dump_chunks.main),
    ]
    if not args.skip_generation:
        stages += [
            ("generation", run_generation.main),
            ("bonus", run_bonus.main),
        ]

    import sys

    started = time.time()
    original_argv = sys.argv
    for name, fn in stages:
        stage_start = time.time()
        print(f"\n{'=' * 70}\n=== {name}\n{'=' * 70}")
        # Each stage parses its own arguments, so hide this runner's flags
        # from it rather than letting argparse reject them.
        sys.argv = [name]
        try:
            fn()
        finally:
            sys.argv = original_argv
        print(f"--- {name} took {time.time() - stage_start:.1f}s")

    print(f"\nAll stages complete in {time.time() - started:.1f}s.")


if __name__ == "__main__":
    main()
