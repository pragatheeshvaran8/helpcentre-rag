"""What the agent carries between steps.

TWO KINDS, AND THEY ARE NOT THE SAME THING
    SHORT TERM is the scratchpad: what I did, what came back. It is rebuilt
    into the prompt every step, so the model can see its own history. It is
    what makes the loop a loop rather than five unrelated questions.

    LONG TERM here is the set of chunks the agent has actually seen. It is not
    fed to the model, it is kept for two other jobs: the final answer is
    grounded in it, and the Week 6 checks read it to decide whether retrieval
    ever put the answer on screen.

WHY THE SCRATCHPAD IS TRIMMED
    A scratchpad that keeps every observation in full grows the prompt on every
    step, and the run dies on token budget before it finishes. Only the last
    `_FULL_STEPS` observations are kept in full. Earlier ones keep the action
    and a one-line note, because what the agent DID stays relevant long after
    the exact text it read stops being.

    That is real memory pressure, not a toy version of it. It is the same
    reason production agents summarise.
"""
from __future__ import annotations

from dataclasses import dataclass, field

# How many recent observations stay in full. Older steps keep their action line
# and a one-line summary only.
_FULL_STEPS = 3
_SUMMARY_CHARS = 160


@dataclass
class Step:
    """One turn of the loop, as it will be shown back to the model."""

    n: int
    thought: str
    tool: str
    args: dict
    observation: str
    ok: bool = True

    def action_line(self) -> str:
        rendered = ", ".join(f"{k}={v!r}" for k, v in (self.args or {}).items())
        return f"{self.tool}({rendered})"


@dataclass
class Memory:
    """The agent's working state for one ticket."""

    steps: list[Step] = field(default_factory=list)
    # Every chunk any tool has surfaced, de-duplicated by chunk_id. This is what
    # the answer must be grounded in, and what the checks score retrieval on.
    seen: dict[str, dict] = field(default_factory=dict)

    def add(self, step: Step, chunks: list[dict]) -> None:
        self.steps.append(step)
        for chunk in chunks:
            self.seen.setdefault(chunk["chunk_id"], chunk)

    @property
    def chunks(self) -> list[dict]:
        """Everything seen, in the order it was first seen."""
        return list(self.seen.values())

    def scratchpad(self) -> str:
        """The history block for the next prompt.

        Recent steps in full, older steps compressed to what was done. Returns
        an empty string on the first step, so the prompt does not open with an
        empty heading.
        """
        if not self.steps:
            return ""
        lines = []
        cutoff = len(self.steps) - _FULL_STEPS
        for i, step in enumerate(self.steps):
            lines.append(f"Step {step.n}")
            if step.thought:
                lines.append(f"  thought: {step.thought}")
            lines.append(f"  action: {step.action_line()}")
            if i < cutoff:
                summary = " ".join(step.observation.split())[:_SUMMARY_CHARS]
                lines.append(f"  result (trimmed): {summary}...")
            else:
                lines.append(f"  result: {step.observation}")
            lines.append("")
        return "\n".join(lines).rstrip()

    def context_blocks(self) -> str:
        """Every chunk seen so far, labelled, for grounding the final answer."""
        if not self.seen:
            return "NO CONTEXT BLOCKS WERE RETRIEVED."
        return "\n\n".join(
            f"[{chunk['chunk_id']}] (article {chunk['article_id']})\n{chunk['text'].strip()}"
            for chunk in self.seen.values()
        )
