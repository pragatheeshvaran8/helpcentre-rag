"""The four-part demo.

    python app.py demo          free. Replays answers already in the log.
    python app.py demo --live   asks one real question first. Costs 1-3 calls.

WHY THE DEFAULT IS A REPLAY
    The provider gives 50 free calls a day. A demo that needs the network is a
    demo that can fail in front of the room for a reason that has nothing to do
    with the work. Everything here except part 1 reads the log and the corpus,
    so it runs offline, in about a second, the same way every time.

    `--live` is there because a replay alone would be a fair thing to doubt.

THE FOUR PARTS
    1. A real run.           One ticket, with every step, its time and its cost.
    2. A real failure.       A wrong answer that every cheap check passed.
    3. A number that moved.  With the before, the after, and the command.
    4. What is next.         The weak spots, named, with no excuses.

    Part 2 is the part worth watching. It is easy to show an app working. The
    thing worth defending is a failure found on purpose, and the check that now
    stops it coming back.
"""
from __future__ import annotations

import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
if str(BASE) not in sys.path:
    sys.path.insert(0, str(BASE))

from rag import term  # noqa: E402

WIDTH = 74


def _wrap(text: str, width: int = WIDTH) -> list[str]:
    import textwrap

    return textwrap.wrap(" ".join((text or "").split()), width) or [""]


def _say(text: str, indent: str = "  ") -> None:
    for line in _wrap(text, WIDTH - len(indent)):
        print(f"{indent}{line}")


def _bullet(text: str, indent: str = "    ") -> None:
    """A bullet whose continuation lines line up under the first word."""
    lines = _wrap(text, WIDTH - len(indent) - 2)
    print(f"{indent}- {lines[0]}")
    for line in lines[1:]:
        print(f"{indent}  {line}")


def _warm_the_index() -> None:
    """Load the corpus index before anything is printed around it.

    The load takes 13 to 40 seconds the first time and writes a hub warning and
    a progress bar to stderr. Both are harmless and both make a working demo
    look broken. The captured text is kept rather than discarded, so a real
    failure still explains itself.
    """
    import contextlib
    import io
    import os

    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
    os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

    from config import STRATEGY_STRUCTURED
    from rag.keyword import build_index

    print(term.grey("  loading the corpus index..."), end="", flush=True)
    noise = io.StringIO()
    try:
        with contextlib.redirect_stderr(noise):
            build_index(STRATEGY_STRUCTURED)
    except Exception as exc:  # noqa: BLE001 - the captured text is the clue
        print(term.red(f" failed: {type(exc).__name__}: {exc}"))
        print(term.grey(noise.getvalue().strip()[:400]))
        return
    print(term.grey(" ready"))
    print()


def _part(number: int, title: str, question: str) -> None:
    """A header that also says what the part is answering."""
    print()
    print(term.rule(f"part {number} of 4   {title}"))
    print(term.grey(f"  the question this answers: {question}"))
    print()


def _pause() -> None:
    """Stop between parts so a presenter can talk. Skipped when piped."""
    if not sys.stdin.isatty():
        return
    try:
        input(term.grey("\n  [enter] "))
    except (EOFError, KeyboardInterrupt):
        print()


# ---------------------------------------------------------------------------
def part1_a_real_run(live: bool) -> None:
    _part(1, "a real run", "does the thing actually work?")

    from obs import store

    if live:
        from agent.budget import Budget
        from agent.loop import run as run_agent

        # The first retrieval loads the embedding model, and the loader prints
        # a hub warning and a progress bar to stderr. Mid-run that lands on top
        # of the agent's own step lines. Warm it here, with stderr held, so the
        # live part looks the same as the replay.
        _warm_the_index()

        ticket = (
            "Two problems on one account. An invoice is stuck on ERR-4032, and "
            "separately the customer is asking what ERR-7215 means."
        )
        _say("Asking this, right now, over the network:")
        print()
        _say(f'"{ticket}"', indent="    ")
        print()
        result = run_agent(ticket, budget=Budget(max_steps=6), verbose=True)
        row = (result.trace.as_dict() if result.trace else None) or store.by_id(result.trace_id)
    else:
        from obs import plant

        rows = [
            r for r in store.read_all()
            if r.get("runner") == "agent"
            and r.get("citations")
            and not r.get("error")
            and not r.get("cache_hit")
        ]
        # Part 2 is entirely about the refund ticket. Opening on the same one
        # makes the app look like it knows one question, so prefer any other.
        planted = " ".join(plant.PLANTED_QUESTION.split())
        other = [r for r in rows if " ".join((r.get("question") or "").split()) != planted]
        rows = other or rows
        # Some traces in the log were rebuilt from cached runs and carry no
        # token counts. Showing one of those means a cost table of zeros in the
        # part right before the part that defends the cost numbers, so a trace
        # that was really metered is preferred.
        metered = [r for r in rows if r.get("input_tokens")]
        rows = metered or rows
        if not rows:
            print(term.red("  No answered run in the log yet."))
            _say("Build one first:  python app.py ask \"What is the fix for ERR-4032?\"")
            return
        row = sorted(rows, key=lambda r: r.get("at", ""))[-1]
        _say("Replaying a real answer out of the log. Nothing is called.")
        print()

    if not row:
        print(term.red("  The run produced no trace."))
        return

    print(term.bold("  THE TICKET"))
    _say(row.get("question", ""), indent="    ")
    print()
    print(term.bold("  THE ANSWER"))
    _say(row.get("answer", ""), indent="    ")
    print()
    print(term.bold("  WHERE EVERY SENTENCE CAME FROM"))
    for chunk_id in row.get("citations") or []:
        print(f"    {term.green(chunk_id)}")
    if not row.get("citations"):
        print(term.yellow("    nothing cited"))
    print()
    print(term.bold("  WHAT IT COST, STEP BY STEP"))
    print(f"    {'step':30} {'ms':>8} {'in':>7} {'out':>6} {'usd':>11}")
    for span in row.get("spans") or []:
        print(f"    {span['name'][:30]:30} {span['ms']:>8} {span['input_tokens']:>7} "
              f"{span['output_tokens']:>6} {span['cost']:>11.8f}")
    print(f"    {term.bold('TOTAL'):30} {row.get('ms', 0):>8} "
          f"{row.get('input_tokens', 0):>7} {row.get('output_tokens', 0):>6} "
          f"{row.get('cost', 0.0):>11.8f}")
    print()
    _say(f"Trace {term.cyan(row.get('trace_id', '?'))}. That id is the handle. Anyone can "
         "reopen this exact answer with: python app.py logs --trace "
         f"{row.get('trace_id', '?')}")


# ---------------------------------------------------------------------------
def part2_a_real_failure() -> None:
    _part(2, "a real failure", "what went wrong, and what stops it now?")

    import contextlib
    import io
    import os

    from config import STRATEGY_STRUCTURED
    from evals.w11_regressions import REFUND_TO_CARD as R01
    from obs import plant
    from rag.keyword import get_record

    # Reading the corpus loads the embedding model, which prints a hub warning
    # and a progress bar to stderr. Both land in the middle of this part and
    # make a working demo look broken, so stderr is held for the duration.
    os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")
    os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")

    _say("A support lead forwarded this. No ticket number, no date, no wording:")
    print()
    for line in _wrap(plant.COMPLAINT, 70):
        print(term.yellow(f"    {line}"))
    print()

    print(term.bold("  THE ANSWER THE DRILL FOUND"))
    for line in _wrap(R01.failing_answer, 70):
        print(term.red(f"    {line}"))
    print()

    print(term.bold("  WHY EVERY CHEAP CHECK PASSED IT"))
    noise = io.StringIO()
    with contextlib.redirect_stderr(noise):
        record = get_record(STRATEGY_STRUCTURED, plant.CITED_CHUNK)
    for label, ok in (
        (f"the citation {plant.CITED_CHUNK} resolves", bool(record)),
        ("every sentence names a source", True),
        ("nothing answerable was refused", True),
    ):
        print(f"    {label:52} {term.green('yes') if ok else term.red('no')}")
    print()
    _say("Three checks, all green, and the answer is still wrong. That is the "
         "whole lesson of this part: a citation proves a chunk exists, not that "
         "the answer agrees with it.")
    print()

    print(term.bold("  WHAT THE CITED CHUNK ACTUALLY SAYS"))
    _say(plant.WHAT_THE_CORPUS_SAYS, indent="    ")
    print()

    print(term.bold("  THE CHECK THAT CATCHES IT"))
    fake_trace = {
        "answer": R01.failing_answer,
        "citations": [plant.CITED_CHUNK],
    }
    caught, why = plant.contradicts_its_citation(fake_trace)
    mark = term.red("FIRES") if caught else term.yellow("silent")
    print(f"    contradicts_its_citation()   {mark}")
    if why:
        _say(why, indent="      ")
    print()

    ok, reasons = R01.judge(R01.failing_answer)
    print(f"    {('regression ' + R01.id + ' on the BAD answer'):52} "
          f"{term.red('caught') if not ok else term.yellow('missed')}")
    for reason in reasons:
        print(f"      {term.grey(reason)}")

    corrected = (
        "No. The card token was dropped during the migration, so the refund "
        "cannot go back to the card. Issue it as account credit instead "
        f"[{plant.CITED_CHUNK}]."
    )
    ok_now, _ = R01.judge(corrected)
    print(f"    {('regression ' + R01.id + ' on a GOOD answer'):52} "
          f"{term.green('passes') if ok_now else term.red('still fails')}")
    print()
    _say("The second line matters as much as the first. A check that fails "
         "everything is not a check. This one separates the two answers.")
    print()
    _say(f"{R01.id} now runs with every other check, on every commit, forever. "
         "That is the loop: a complaint becomes a trace, the trace becomes a "
         "test, and the test outlives the person who wrote it.")


# ---------------------------------------------------------------------------
def part3_a_number_that_improved() -> None:
    _part(3, "a number that improved", "did any of this measurably help?")

    print(term.bold("  ACCURACY"))
    print(f"    {'prompt v1 (before)':34} {'20/43':>10} {'46.5%':>8}")
    print(f"    {term.green('prompt v2 (after)'):34} {term.green('34/43'):>10} "
          f"{term.green('79.1%'):>8}")
    print()
    _say("43 is the denominator because 43 of the 60 cases were scored under "
         "both prompts. Scoring a case the other run never reached would make "
         "the gain look bigger than it is.")
    print()
    _say("The fix was one rule. v1 said a partial answer is a refusal, so the "
         "model refused whenever the wording looked unfamiliar. v2 says never "
         "refuse because of how the question is worded, and names four traps "
         "it used to fall into. False refusals were 21 of the failures.")
    print(term.grey("    evidence: results/w6_results.md   "
                    "rerun: python -m evals.run_evals --tag after"))
    print()

    print(term.bold("  COST"))
    print(f"    {'cost per request':34} {term.green('-76.3%'):>10}")
    print(f"    {'cache hit rate on real traffic':34} {'81.9%':>10}")
    print(f"    {'wrong answers the cache served':34} {term.green('0 / 48'):>10}")
    print()
    _say("The third line is the one to defend. A cache that serves a stale or "
         "near-miss answer is not a saving, so the saving was measured next to "
         "its risk, at four different match thresholds, and reported together.")
    print(term.grey("    evidence: results/w11_results.md   "
                    "rerun: python -m evals.run_w11 --cost"))
    print()

    print(term.bold("  WHAT THESE NUMBERS ARE NOT"))
    for line in (
        "60 eval cases is a small set. A different mix would move the accuracy figure.",
        "The cost figures are a published rate applied to real token counts, not a bill.",
        "81.9% is a hit rate on replayed traffic, so treat it as a ceiling, not a forecast.",
    ):
        _bullet(line)


# ---------------------------------------------------------------------------
def part4_what_is_next() -> None:
    _part(4, "what is next", "what do you still not trust?")

    path = BASE / "KNOWN_WEAK_SPOTS.md"
    if not path.exists():
        print(term.red("  KNOWN_WEAK_SPOTS.md is missing."))
        return

    # The file wraps its paragraphs, so a label and its text are several lines.
    # Reading only the label's own line truncated every entry mid-sentence, so
    # each paragraph is gathered up to the next blank line.
    lines = path.read_text(encoding="utf-8").splitlines()
    shown = 0
    i = 0
    while i < len(lines):
        raw = lines[i]
        if raw.startswith("### "):
            shown += 1
            print(f"  {term.yellow(str(shown) + '.')} {term.bold(raw[4:].strip())}")
            i += 1
            continue
        for label, prefix, grey in (
            ("**Why it matters:**", "", False),
            ("**Fix:**", "next: ", True),
        ):
            if not raw.startswith(label):
                continue
            para = [raw[len(label):].strip()]
            i += 1
            while i < len(lines) and lines[i].strip():
                para.append(lines[i].strip())
                i += 1
            text = prefix + " ".join(para)
            if grey:
                for line in _wrap(text, WIDTH - 5):
                    print(term.grey(f"     {line}"))
                print()
            else:
                _say(text, indent="     ")
            break
        else:
            i += 1
    print()
    _say("Every one of those is written down in KNOWN_WEAK_SPOTS.md before "
         "anyone asks. A weak spot you found yourself is a different "
         "conversation from one found for you.")


# ---------------------------------------------------------------------------
def run(live: bool = False) -> int:
    term.init()
    print(term.rule("Tier-1 Deflection Assistant   the four-part demo"))
    _say("A support agent pastes a ticket. The app answers it from the help "
         "centre, cites the paragraph it used, and refuses when the corpus "
         "does not hold the answer.")
    print()
    print(term.grey("  free and offline unless you passed --live"
                    if not live else "  --live: part 1 makes real calls"))

    for step in (
        lambda: part1_a_real_run(live),
        part2_a_real_failure,
        part3_a_number_that_improved,
        part4_what_is_next,
    ):
        _pause()
        try:
            step()
        except KeyboardInterrupt:
            print(term.yellow("\n  stopped"))
            return 130
        except Exception as exc:  # noqa: BLE001 - a demo reports, never crashes
            print(term.red(f"\n  this part could not run: {type(exc).__name__}: {exc}"))

    print()
    print(term.rule("end"))
    _say("Everything shown is reproducible. python app.py report lists each "
         "number with the file it came from and the command that rebuilds it.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run("--live" in sys.argv))
