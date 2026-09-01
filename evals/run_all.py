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
    parser.add_argument(
        "--week",
        choices=("3", "4", "5", "all"),
        default="all",
        help="Which week's evaluation to run. Default: all.",
    )
    args = parser.parse_args()

    from rag import ingest
    from evals import (
        dump_chunks,
        run_bonus,
        run_filter_demo,
        run_generation,
        run_search_eval,
        w4_failures,
        w4_measure,
        w5_collect,
        w5_taxonomy,
    )

    want3 = args.week in ("3", "all")
    want4 = args.week in ("4", "all")
    want5 = args.week in ("5", "all")

    stages: list[tuple[str, callable]] = []
    if not args.skip_ingest:
        stages.append(("ingest", ingest.main))
    if want3:
        stages += [
            ("w3 search evaluation", run_search_eval.main),
            ("w3 filter demo", run_filter_demo.main),
            ("w3 chunk dump", dump_chunks.main),
        ]
        if not args.skip_generation:
            stages += [
                ("w3 generation", run_generation.main),
                ("w3 bonus", run_bonus.main),
            ]
    if want4:
        # The headline before-and-after. Search only, so it always runs.
        stages.append(("w4 hit-rate@3 before/after", w4_measure.main))
        if not args.skip_generation:
            stages.append(("w4 failure separation", w4_failures.main))
    if want5:
        # Collecting traces IS a generation stage; there is no trace without an
        # answer in it. The taxonomy reads the traces already on disk, so it
        # still runs and still rebuilds its write-up without an API key.
        if not args.skip_generation:
            stages.append(("w5 trace collection", w5_collect.main))
        stages.append(("w5 taxonomy and prediction", w5_taxonomy.main))

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
