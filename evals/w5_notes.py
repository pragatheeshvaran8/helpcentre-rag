"""Week 5 step 2: one honest sentence per trace, written by hand.

THIS FILE IS THE PART THAT CANNOT BE AUTOMATED
    Everything else in Week 5 is a script. This is not. Each note below was
    written after reading that trace in results/w5_traces.md: the question, the
    three chunks that came back, the context that was sent, and the answer that
    came out.

WRITTEN BEFORE ANY GROUP EXISTED
    The notes came first and the groups came from the notes, not the other way
    round. That ordering is the whole point. Deciding the categories first means
    finding the problems you expected instead of the problems you have.

    You do not have to take that on trust. No note below contains the name of
    any group in evals/w5_taxonomy.py, and the acceptance suite asserts it. A
    note that named a group would be a note written backwards from the answer.

WHY THERE IS A NOTE FOR EVERY TRACE, NOT ONLY THE FAILURES
    The task asks for a note per failure. All 20 are noted anyway, because a
    file holding only the 6 failures cannot show that the other 14 were read.
    The passes are also where the near-misses are: T11 records a look-alike
    error code taking the top rank, and that trace passed retrieval.

WHAT A NOTE IS ALLOWED TO BE
    One sentence. What happened, in plain words. No cause, no category, no fix.
    "The model refused although the answer was the top chunk" is a note.
    "Over-refusal caused by prompt rule 5" is a diagnosis, and diagnosing this
    early is guessing.
"""
from __future__ import annotations

# trace_id -> the sentence written while reading that trace.
NOTES: dict[str, str] = {
    "T01": "Both halves of the question were answered out of one chunk and both "
           "sentences carried the same citation.",

    "T02": "The model printed the fixed refusal block, then wrote \"Wait, let me "
           "re-read the context blocks\", changed its mind, and gave the correct "
           "answer underneath it, so the app reported a refusal for an answer "
           "that was sitting right there.",

    "T03": "A missing ERR prefix and a misspelt word did not stop it; the right "
           "row came back first and the answer was right.",

    "T04": "The answer is correct and lifted almost word for word from the top "
           "chunk, but not one sentence carries a chunk id, so nothing in it can "
           "be checked.",

    "T05": "It refused, and the Missing line asked for the error code, which is "
           "exactly the thing the agent has to supply.",

    "T06": "Two separate API changes were both answered from a single endpoint "
           "table, and both were cited.",

    "T07": "It refused a question that has no subject in it, and asked what the "
           "scenario was.",

    "T08": "Nothing in the corpus covers incident SLAs and it refused without "
           "inventing one.",

    "T09": "The meaning and the agent action were both right, but in place of a "
           "chunk id it wrote \"the migration status codes table\" in words, so "
           "the answer cannot be verified.",

    "T10": "The row holding the exact fix was the top chunk and the model still "
           "refused, saying it had no step-by-step walkthrough.",

    "T11": "The answer was in the context at rank 2 and the model refused; a tax "
           "row whose code looks similar took rank 1 ahead of it.",

    "T12": "One sentence, the right figure, a citation, nothing to fault.",

    "T13": "It answered the question that was actually asked, whether an invoice "
           "is affected, instead of reciting the whole table row.",

    "T14": "It refused, and the Missing line shows it read the layout-explanation "
           "chunk and judged it not an answer to an angry customer.",

    "T15": "Both parts were answered and it carried across the warning about "
           "checking for a double charge.",

    "T16": "Short, right, cited.",

    "T17": "It carried across the \"do not retry\" warning that sits in the same "
           "table cell, which is the part an agent would most easily miss.",

    "T18": "It explained why the number is invalid now, added the revalidation "
           "step from a second chunk, and cited both.",

    "T19": "The whole answer was in the first chunk word for word and the model "
           "refused; the question asked \"can I\" and the corpus phrases it as "
           "what the agent should do instead.",

    "T20": "It refused a message that carries no detail at all, and asked what "
           "was broken.",
}


def note_for(trace_id: str) -> str:
    return NOTES[trace_id]


if __name__ == "__main__":
    for trace_id, note in NOTES.items():
        print(f"{trace_id}  {note}")
    print(f"\n{len(NOTES)} notes")
