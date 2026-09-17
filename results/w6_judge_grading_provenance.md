# Provenance of the judge-validation grades

**These grades were drafted by an AI assistant, not graded independently by a
human from scratch.**

That matters, and it must not be glossed over. The Week 6 mentor checklist asks:

> "If they used an AI judge, did they check it agrees with **their own**
> grading first?"

An AI drafting the grades weakens that claim. One model checking another model
is not the independent check the question is asking for.

## How the grades were reached

For each of the 20 cases the assistant read three things: the question, the
answer, and the exact text of the chunks the answer cited. Then it applied two
rules.

- **faithful = n** when no source was cited at all, or when the cited chunk does
  not contain the fact the answer states.
- **relevant = n** when the answer addresses a different question from the one
  asked.

Every row carries its reason in the `note` column, so each verdict can be
checked against the source without rerunning anything.

## What still needs to happen

Read the 20 reasons and change any you disagree with. Once you have reviewed
them, they are your grades and the checklist question can be answered honestly.
Until then, this file is the caveat that belongs in the write-up.

## The one genuinely arguable call

Four cases cited no source at all: P02, P06, P22 and P35. Their content is
correct, and it matches the corpus. They were marked **faithful = n** on the
reading that an answer with nothing to check against cannot be called
supported.

The opposite reading is defensible: the claims are true, so the answer is
faithful even though unsourced. If you take that view, change those four to
**y**. It will change the agreement number, which is exactly why the call
belongs to you and not to the assistant.
