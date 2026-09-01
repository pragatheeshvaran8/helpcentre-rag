# Week 5 — problem taxonomy and the one thing to fix next

Built from [`evals/w5_notes.py`](../evals/w5_notes.py), which was written while reading [`w5_traces.md`](w5_traces.md) and before any group existed.

## The sample in one line

20 traces read. 14 passed, 6 failed. 15 should have been answered, 5 should have been refused.

**Retrieval was correct in every single failure.** All 15 answerable traces put the answering chunk inside the top 3, and 6 of them still came out wrong. The Week 4 metric scores this sample 100 percent.

## How severity was judged

| Severity | Meaning |
|---|---|
| 3 | The agent cannot tell a right answer from a wrong one. Wrong or unsourced information can reach the customer looking exactly like sourced information. |
| 2 | The agent gets nothing they can act on and has to work around the app. Nothing wrong reaches the customer; the app's usefulness is what is lost. |
| 1 | The answer is right and checkable, only clumsier to use than it should be. |

## The ranking

| Rank | Problem | How often | Severity | Score | Traces |
|---|---|---|---|---|---|
| 1 | Answers with nothing you can check | 2 of 20 | 3 | **6** | T04, T09 |
| 2 | Refuses a question the corpus can answer **<- chosen** | 3 of 20 | 2 | **6** | T10, T11, T19 |
| 3 | Prints a refusal, then answers anyway | 1 of 20 | 2 | **2** | T02 |

**The top 2 are tied on 6.** “Answers with nothing you can check” and “Refuses a question the corpus can answer” score the same, and the tie is real rather than something to round away.

**Tie-break rule.** Attack the group that leaves the agent with nothing at all. A correct answer with a missing citation still carries the answer, and an agent can check it against the chunks on screen. A refusal carries nothing, and an agent refused twice stops opening the tool. That is the failure that ends the product.

---

## The groups

### Answers with nothing you can check

**Traces:** T04, T09 · **How often:** 2 of 20 · **Severity:** 3 · **Score:** 6

**What you see.** A fluent, correct answer with no [chunk_id] anywhere in it. T09 goes further and names its source in words, "the migration status codes table", which looks like a citation and cannot be resolved.

**Why we think it happens.** Prompt rule 1 requires a citation on every sentence and the model simply does not comply on some answers. Nothing in the app enforces it afterwards: verify_citations checks the ids that ARE present and has nothing to say about an answer with none.

**Fix direction.** Enforce it in code rather than asking again. An answer with zero resolvable citations is not an answer, and should be handled the way an unresolvable citation already is.

**The notes this group came from**

- **T04** (P23, `symptom`): The answer is correct and lifted almost word for word from the top chunk, but not one sentence carries a chunk id, so nothing in it can be checked.
- **T09** (P42, `multi_part`): The meaning and the agent action were both right, but in place of a chunk id it wrote "the migration status codes table" in words, so the answer cannot be verified.

---

### Refuses a question the corpus can answer

**Traces:** T10, T11, T19 · **How often:** 3 of 20 · **Severity:** 2 · **Score:** 6

**What you see.** The app returns the fixed refusal, and the Missing line names something the corpus really does contain. In all three the answering chunk was in the context the model was shown.

**Why we think it happens.** The three questions ask for a SHAPE the corpus does not have, while asking for SUBSTANCE it does have. T10 asked to be walked through a procedure and the corpus has a one-line fix. T19 asked "can I" and the corpus states what the agent should do instead. T11 asked about a code sitting at rank 2 behind a look-alike code. Prompt rule 5 makes a partial answer a refusal, and the model appears to read a shape mismatch as a partial answer.

**Fix direction.** One prompt change: say that a refusal is about missing FACTS, never about the question's wording, and that an answer covering the substance in fewer steps than asked for is still an answer.

**The notes this group came from**

- **T10** (P34, `procedure`): The row holding the exact fix was the top chunk and the model still refused, saying it had no step-by-step walkthrough.
- **T11** (P02, `code_lookup`): The answer was in the context at rank 2 and the model refused; a tax row whose code looks similar took rank 1 ahead of it.
- **T19** (P31, `policy`): The whole answer was in the first chunk word for word and the model refused; the question asked "can I" and the corpus phrases it as what the agent should do instead.

---

### Prints a refusal, then answers anyway

**Traces:** T02 · **How often:** 1 of 20 · **Severity:** 2 · **Score:** 2

**What you see.** The reply opens with the exact refusal block, continues "Wait, let me re-read the context blocks", and then gives the correct answer. The app reads the refusal token and reports a refusal, so the correct answer underneath is thrown away.

**Why we think it happens.** Prompt rule 4 says reply with the refusal 'and nothing else'. The model treats the refusal as a first draft it may revise. The app assumes the token can only appear in a real refusal, so one self-correcting reply is enough to break the contract.

**Fix direction.** Decide the refusal on the whole reply, not the opening line. A reply that contains the refusal token AND a resolvable citation is not a refusal, and should be treated as a prompt violation to be seen, not silently converted into one.

**The notes this group came from**

- **T02** (P17, `code_lookup`): The model printed the fixed refusal block, then wrote "Wait, let me re-read the context blocks", changed its mind, and gave the correct answer underneath it, so the app reported a refusal for an answer that was sitting right there.

---

## What is NOT a group

Two things were tempting and are left out, because no trace failed on them.

- **A look-alike code taking the top rank.** In T11 the vector arm put the ERR-7302 tax row first, ahead of the ERR-4032 row the question asked about. The BM25 arm pulled the right chunk to rank 2, so retrieval passed and the refusal is what failed. Worth watching, not worth fixing yet.
- **Refusals on under-specified questions.** All 5 came out right, and their Missing lines named the detail an agent has to supply. Calling this a problem would mean the app is wrong for doing the thing it was built to do.

---

## The target: Refuses a question the corpus can answer

**The change.** One prompt change: separate 'the facts are not in the context' from 'the question is worded in a shape the corpus does not use', and allow a refusal only for the first.

**Why it should work.** All three failures had the answering chunk in the context. Nothing was missing except a licence to answer, so no retrieval change can move this number and a prompt change should move all of it.

**Where it gets measured.** The whole 60-question pool, not just the 20 traces that were read. 40 of the 60 have never been run. Measuring only the traces that produced the hypothesis would be marking my own homework.

## The prediction, written before the change

| Metric | Now | Predicted after | Falsified if |
|---|---|---|---|
| False refusals among the 15 answerable traces read | 3 of 15 | 0 or 1 of 15 | still 3 of 15 |
| False refusals across all 53 answerable pool questions | not measured; 38 of them have never been run | under 10 percent, so 5 or fewer of 53 | 10 percent or more |
| Correct refusals across all 7 pool questions that should be refused | 5 of 5 among those read; the other 2 have never been run | 6 or 7 of 7 | 5 or fewer of 7 |
| Answers with zero citations among the 15 answerable traces read | 2 of 15 | no worse than 2 of 15 | 3 or more of 15 |

**The guard.** The third metric is the one that stops a cheap win. Loosening the refusal rule until nothing is ever refused would clear metrics 1 and 2 and wreck the app. If correct refusals fall, the change has failed even if false refusals go to zero.

**The confound to control.** The generation model is a free tier and this project has already had to change model once mid-way. Before and after MUST be measured in the same session, on the same model, with the same corpus_sha. A before-number carried over from a different day is not a baseline.

## Self-check

| Check | Result |
|---|---|
| Every failing trace is in exactly one group | yes |
| No passing trace was put in a group | yes |
| Every grouped trace has a hand-written note | yes |
