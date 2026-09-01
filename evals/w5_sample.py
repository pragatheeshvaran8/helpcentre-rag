"""Week 5 sampling: draw 20 traces from the pool of 60, fairly.

WHY THIS FILE EXISTS AT ALL
    The single easiest way to fake an error analysis is to pick the 20 traces
    you already understand. The mentor checklist asks about it directly: did
    they read a fair sample, not just the good examples?

    So the draw is not a judgement. It is one line of standard library:

        random.Random(W5_SEED).sample(ids, 20)

    Anybody can rerun it and get the same 20. Nothing about the app, the
    question text, or how well it performed touches the selection.

ABOUT THE SEED
    W5_SEED is 5, the week number. It was fixed before the first draw and has
    never been changed. That matters: trying seeds until the sample looks good
    is cherry-picking with extra steps, and a seed with an arbitrary-looking
    value invites exactly that suspicion.

WHY NOT STRATIFY BY KIND
    Stratifying would guarantee, say, two multi-part questions and one vague
    one. It sounds fairer and is not. Choosing the strata is choosing the
    answer, and it hides how common each kind of traffic is in the pool. A
    uniform draw lets the sample be lumpy, which real samples are. The write-up
    reports the lumpiness instead of engineering it away.

WHY 20
    The task asks for around 20 traces read by hand. 20 out of a 60 pool is a
    third of it, which is enough to see repeated problems and small enough to
    read every trace properly. A sample nobody actually reads is worse than a
    smaller one.
"""
from __future__ import annotations

import random

from evals.w5_questions import POOL_BY_ID, W5_POOL

# The week number. Fixed before the first draw, never changed since.
W5_SEED = 5

# How many traces get read by hand.
W5_SAMPLE_SIZE = 20


def draw_ids(size: int = W5_SAMPLE_SIZE, seed: int = W5_SEED) -> list[str]:
    """The sampled question ids, in draw order. Deterministic."""
    ids = [q["id"] for q in W5_POOL]
    return random.Random(seed).sample(ids, size)


def draw(size: int = W5_SAMPLE_SIZE, seed: int = W5_SEED) -> list[dict]:
    """The sampled questions, in draw order."""
    return [POOL_BY_ID[qid] for qid in draw_ids(size, seed)]


def composition(questions: list[dict]) -> dict[str, int]:
    """How many of each traffic kind a list of questions holds."""
    counts: dict[str, int] = {}
    for q in questions:
        counts[q["kind"]] = counts.get(q["kind"], 0) + 1
    return counts


def audit_table() -> str:
    """Markdown showing the pool against the drawn sample, kind by kind.

    Printed into the write-up so a reader can see what the draw over-picked and
    under-picked without taking anybody's word for it.
    """
    sample = draw()
    pool_counts = composition(W5_POOL)
    sample_counts = composition(sample)

    lines = [
        f"Seed `{W5_SEED}`, drawn with `random.Random(seed).sample(ids, {W5_SAMPLE_SIZE})` "
        f"over the pool in file order.",
        "",
        "| Traffic kind | In pool | Drawn | Expected at 1/3 |",
        "|---|---|---|---|",
    ]
    for kind, in_pool in pool_counts.items():
        drawn = sample_counts.get(kind, 0)
        expected = in_pool * W5_SAMPLE_SIZE / len(W5_POOL)
        lines.append(f"| `{kind}` | {in_pool} | {drawn} | {expected:.1f} |")
    lines.append(f"| **total** | **{len(W5_POOL)}** | **{len(sample)}** | |")
    lines.append("")
    lines.append("Drawn ids, in draw order: " + ", ".join(f"`{q['id']}`" for q in sample))
    return "\n".join(lines)


if __name__ == "__main__":
    print(audit_table())
    print()
    for i, q in enumerate(draw(), start=1):
        print(f"{i:>2}. {q['id']}  [{q['kind']}]  expect {q['expected_behaviour']}")
        print(f"    {q['question']}")
