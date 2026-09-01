# Week 5 — Error Analysis: reading traces instead of trusting a score

**Headline:** retrieval was **perfect** on this sample, 15 of 15, and the app
still got **6 of 20 answers wrong**. Every single failure happened after the
right chunk was already on screen. The Week 4 metric scores this sample 100
percent and cannot see any of it.

> **Note on the corpus and the questions.** The 6 articles were written for this
> exercise and so was the 60-question traffic pool. The billing system, the error
> codes and the dates are invented. Nothing here documents a real product.

---

## 0. What this week produced

| Deliverable | Where |
|---|---|
| 20 complete traces, as collected | [`w5_traces.md`](w5_traces.md) |
| One honest note per trace, hand-written | [`../evals/w5_notes.py`](../evals/w5_notes.py) |
| Named problem groups, ranked, with a target | [`w5_taxonomy.md`](w5_taxonomy.md) |
| The prediction, written before the fix | [`w5_taxonomy.md`](w5_taxonomy.md#the-prediction-written-before-the-change) |

Nothing was changed in the app this week. Week 5 is a measurement, and a
measurement taken while you are also fixing things measures nothing.

---

## 1. The result that matters

| | Count |
|---|---|
| Traces read | 20 |
| Passed | 14 |
| Failed | **6** |
| Answerable questions where retrieval put the answer in the top 3 | **15 of 15** |
| Questions that should have been refused, and were | **5 of 5** |
| Failures where retrieval had already found the answer | **6 of 6** |

Read the last two rows together.

Week 4 finished by driving hit-rate@3 from 28/30 to 30/30 and emptying the
"wrong document fetched" bucket. That work holds. On this sample retrieval never
missed once. **And the app was still wrong 6 times out of 20.**

Every failure this week is the same shape: the answering chunk was in the context
the model was shown, and something went wrong afterwards. No amount of further
retrieval work can touch any of them.

---

## 2. What a complete trace is

A trace is complete when somebody else can replay the answer months later without
asking a single question. Three groups of fields, defined in
[`evals/w5_trace.py`](../evals/w5_trace.py):

| Group | Fields |
|---|---|
| **The exact input** | the question, and the pool id it was drawn from |
| **The exact machinery** | strategy, collection, retrieval mode, k, gate threshold, embedding model, chunk size, chunk count, RRF and BM25 constants, LLM name, temperature, reply cap, **prompt hash**, **corpus hash** |
| **The exact output** | every retrieved chunk with rank and per-arm ranks and full text, the context string that was really sent, the raw answer, every citation and whether it resolves, refused, gate_fired, budget_degraded, latency |

Two of those fields are the easy ones to leave out and they are the ones that
hurt.

- **Without the prompt hash and the corpus hash**, "I cannot reproduce this" has
  no answer, because the two things most likely to have drifted are invisible.
- **Without the context string**, you cannot tell a retrieval failure from a
  reading failure. That distinction is the entire week.

Every trace carries its own copy of the settings rather than pointing at
`config.py`, so a trace stays true to the run that made it after the config
changes.

### The traces are provably replayable

The acceptance suite does not take this on trust. It re-grades all 20 traces
using only what the JSON file holds plus the index, and checks the rebuilt grade
matches the stored one. It also checks every retrieved `chunk_id` still resolves.
If a trace were missing something that mattered, the rebuild would disagree.

---

## 3. The sample is drawn, not chosen

The easiest way to fake an error analysis is to read the 20 traces you already
understand. So selection is not a judgement anywhere in this week:

```python
random.Random(5).sample(ids, 20)      # evals/w5_sample.py
```

- The pool is **60 questions**, written before any of them was run, and not
  edited since the first trace was collected.
- The seed is **5**, the week number. Fixed before the first draw, never changed.
  Trying seeds until the sample looks good is cherry-picking with extra steps.
- The draw is **uniform over all 60**. It is deliberately not stratified by
  traffic kind, because choosing the strata is choosing the answer.

### The pool is written like real traffic, not like an exam

| Traffic kind | In pool | Drawn | Expected at 1/3 |
|---|---|---|---|
| `code_lookup` — an agent pastes the code | 18 | 6 | 6.0 |
| `symptom` — customer wording, no code | 8 | 2 | 2.7 |
| `policy` — "can I do this" | 7 | 2 | 2.3 |
| `procedure` — "how do I actually do it" | 6 | 1 | 2.0 |
| `multi_part` — two questions in one message | 6 | 3 | 2.0 |
| `noisy` — typos, missing prefixes | 5 | 1 | 1.7 |
| `vague` — under-specified | 4 | 4 | 1.3 |
| `cross_article` — answer spans two articles | 3 | 0 | 1.0 |
| `out_of_corpus` — genuinely not covered | 3 | 1 | 1.0 |
| **total** | **60** | **20** | |

**The draw came out lumpy, and it is left lumpy.** It took all 4 vague questions
when 1.3 was expected, and took no cross-article question at all. That is what an
honest uniform draw looks like on 20 items. Re-rolling the seed to get a
prettier table would destroy the only property that makes the sample worth
anything.

**What that costs, stated plainly:** cross-article questions are untested this
week, and vague questions are over-represented, which flatters the refusal
numbers because all 4 of them are supposed to be refused. Section 7 says what
to do about it.

### Why the questions had to be new

Week 4's set is one clean question per error code. Real agents do not type like
that. This pool has pasted codes, customer wording with no code, two questions
in one message, `invocie error 4010 addres missing`, and questions the corpus
cannot answer at all.

Every required answer string is verbatim from an article, and the acceptance
suite checks that **every requirement is satisfiable by a single chunk**. A
question that could not be answered by construction would manufacture a fake
failure, and there are none.

---

## 4. Open coding: notes first, categories second

Every trace got **one honest sentence**, written while reading it, before any
group existed. All 20, not only the 6 failures, because a file holding only the
failures cannot show that the rest were read.

A note says what happened. It does not say why, and it does not name a category:

> **T10:** The row holding the exact fix was the top chunk and the model still
> refused, saying it had no step-by-step walkthrough.
>
> **T04:** The answer is correct and lifted almost word for word from the top
> chunk, but not one sentence carries a chunk id, so nothing in it can be
> checked.
>
> **T11:** The answer was in the context at rank 2 and the model refused; a tax
> row whose code looks similar took rank 1 ahead of it.

The ordering claim is checkable rather than a promise. **No note contains the
name of any group**, and the acceptance suite asserts it. A note that named a
group would be a note written backwards from the conclusion.

Full set: [`evals/w5_notes.py`](../evals/w5_notes.py).

---

## 5. The problem groups

Three groups came out of those notes. Names are written so a stranger knows what
went wrong without opening the repo.

### Severity, judged the same way every time

Frequency is counted. Severity is a judgement, so the ladder is written down once
and applied to every group.

| Severity | Meaning |
|---|---|
| **3** | The agent cannot tell a right answer from a wrong one. Wrong or unsourced information can reach the customer looking exactly like sourced information. |
| **2** | The agent gets nothing they can act on and has to work around the app. Nothing wrong reaches the customer; the app's usefulness is what is lost. |
| **1** | The answer is right and checkable, only clumsier to use than it should be. |

### The ranking

| Rank | Problem | How often | Severity | Score | Traces |
|---|---|---|---|---|---|
| 1 | Answers with nothing you can check | 2 of 20 | 3 | **6** | T04, T09 |
| 2 | Refuses a question the corpus can answer **← chosen** | 3 of 20 | 2 | **6** | T10, T11, T19 |
| 3 | Prints a refusal, then answers anyway | 1 of 20 | 2 | **2** | T02 |

**The top two are tied at 6, and the tie is left standing.** Rounding it away
with a hidden sort key would hide a real decision.

**Tie-break rule.** Attack the group that leaves the agent with nothing at all.
A correct answer with a missing citation still carries the answer, and an agent
can check it against the chunks on screen. A refusal carries nothing, and an
agent refused twice stops opening the tool.

### 1. Answers with nothing you can check — 2 traces, severity 3

A fluent, correct answer with no `[chunk_id]` anywhere in it. T09 goes further
and names its source in words, "the migration status codes table", which looks
like a citation and cannot be resolved.

Both answers happened to be right. That is luck, not a property. An invented
answer would look exactly the same, which is the whole reason the forced-citation
design exists. Nothing in the app catches it: `verify_citations` checks the ids
that *are* present and has nothing to say about an answer with none.

### 2. Refuses a question the corpus can answer — 3 traces, severity 2

The app returns the fixed refusal and the `Missing:` line names something the
corpus really does contain. In all three the answering chunk was in the context.

The pattern: these questions ask for a **shape** the corpus does not have, while
asking for **substance** it does have.

| Trace | The question asked for | The corpus has |
|---|---|---|
| T10 | "walk me through" a procedure | a one-line fix in a table cell |
| T19 | "can I give them an extension" | what the agent should do instead |
| T11 | `ERR-4032`, sitting at rank 2 | the row, behind a look-alike tax code |

Prompt rule 5 says a partial answer is a refusal. The model appears to read a
shape mismatch as a partial answer.

### 3. Prints a refusal, then answers anyway — 1 trace, severity 2

T02 is worth quoting in full, because a summary makes it sound impossible:

```
REFUSED: The help-centre corpus does not contain this information.
Missing: The specific change required to resolve ERR-7215.

Wait, let me re-read the context blocks to verify.

Actually, looking at the context blocks again, I can see that
[HC-4005-structured-003] contains information about ERR-7215. ...
update the legal entity name on the account to match the registration
exactly, then revalidate. [HC-4005-structured-003]
```

The model treated the fixed refusal block as a first draft it could revise. The
app checks the refusal token, sees it, and throws the correct answer underneath
away. Prompt rule 4 says "reply with exactly this, and nothing else", and the app
was built assuming that rule holds.

### What is deliberately NOT a group

- **A look-alike code taking the top rank.** In T11 the vector arm put the
  `ERR-7302` tax row ahead of the `ERR-4032` row the question asked about. BM25
  pulled the right chunk to rank 2, retrieval passed, and the refusal is what
  failed. Worth watching. Not worth fixing while zero traces fail on it.
- **Refusals on under-specified questions.** All 5 were correct, and their
  `Missing:` lines named the detail the agent has to supply. Calling that a
  problem would mean the app is wrong for doing what it was built to do.

---

## 6. The one thing to fix next, and the prediction

**Target: Refuses a question the corpus can answer.**

**The change.** One prompt change. Separate "the facts are not in the context"
from "the question is worded in a shape the corpus does not use", and allow a
refusal only for the first.

**Why it should work.** All three failures had the answering chunk in the
context. Nothing was missing except a licence to answer. No retrieval change can
move this number, and a prompt change should move all of it.

**Where it gets measured.** The whole 60-question pool, not the 20 traces the
hypothesis came from. **40 of the 60 have never been run.** Measuring only the
traces that produced the hypothesis would be marking my own homework.

### Written before the change is made

| Metric | Now | Predicted after | Falsified if |
|---|---|---|---|
| False refusals among the 15 answerable traces read | 3 of 15 | 0 or 1 of 15 | still 3 of 15 |
| False refusals across all 53 answerable pool questions | not measured; 38 never run | under 10%, so 5 or fewer of 53 | 10% or more |
| Correct refusals across all 7 pool questions that should be refused | 5 of 5 among those read; other 2 never run | 6 or 7 of 7 | 5 or fewer of 7 |
| Answers with zero citations among the 15 answerable traces read | 2 of 15 | no worse than 2 of 15 | 3 or more of 15 |

**The guard.** Row 3 is the row that stops a cheap win. Loosening the refusal
rule until nothing is ever refused would clear rows 1 and 2 and wreck the app.
If correct refusals fall, the change has failed even if false refusals reach
zero.

**The confound to control.** The generation model is a free tier, and this
project already had to change model once mid-way through Week 4. Before and after
**must** be measured in the same session, on the same model, with the same
`corpus_sha`. A before-number carried over from another day is not a baseline.

---

## 7. What this week does NOT tell you

The more useful half, as in Week 4.

**Cross-article questions were never tested.** The draw took none of the 3 in
the pool. Multi-part questions inside one article passed (T01, T06), but a
question needing two articles at k=3 is a different problem and this week has
zero evidence about it. The fix is to draw a second sample with a different seed,
not to quietly add the cross-article questions to this one.

**Vague questions are over-represented.** 4 drawn against 1.3 expected, and all 4
are supposed to be refused. That flatters the 5-of-5 refusal number. The real
refusal accuracy is measured on 5 questions, which is not many.

**One model, one day.** Every trace ran on `poolside/laguna-s-2.1:free` at
temperature 0. Three groups here are all failures to follow the output contract,
and contract-following is exactly what varies most between models. A different
model could have a completely different taxonomy. Nothing here is a claim about
RAG in general.

**20 traces is 20 traces.** A group with 1 trace (T02) is an anecdote, not a
rate. It is ranked last for that reason, and it is in the taxonomy at all only
because the failure mode is one nobody would guess.

**Three provider rate-limit errors were retried, not counted.** The first
collection run lost 3 traces to a 429 on the free tier's 20-per-minute cap. Those
were re-run rather than recorded, because the provider's quota is not the app
being wrong. The collector now waits 4 seconds between calls. Traces are stored
with an `error` outcome that is honestly distinguishable from a failure, and the
acceptance suite checks none was left in that state.

**The severity numbers are a judgement.** The ladder is written down and applied
the same way to all three groups, which makes it checkable, not objective. Move
"answers with nothing you can check" to severity 2 and the ranking changes.

---

## 8. Benchmarks against your own app

The syllabus asks how MMLU and HumanEval relate to this. This week answers it
with a number rather than an opinion.

**A benchmark scores the model. This app's failures are not the model's
knowledge.**

All 6 failures happened with the correct answer already inside the context
window. Not one is a knowledge question, a reasoning question, or a coding
question. They are:

- refusing text that is on screen (3)
- omitting a required citation (2)
- ignoring a "reply with exactly this" instruction (1)

MMLU cannot measure any of those, because MMLU never puts a retrieved chunk in
front of the model and never asks it to obey an output contract. A model that
scores 5 points higher on MMLU could easily do worse here.

**The sharper version of the same point is inside this repo.** Week 4's metric,
hit-rate@3, is the closest thing this project has to a benchmark:

| Measure | This sample |
|---|---|
| hit-rate@3, the Week 4 headline metric | **15 of 15, a perfect score** |
| Answers an agent could actually use | **14 of 20** |

A metric at 100 percent, sitting next to an app that is wrong 30 percent of the
time. That gap is not a flaw in hit-rate@3. It is what every benchmark does: it
measures the slice it was built for and says nothing about the rest.

**What replaces it.** Not a better benchmark. Twenty traces read by hand, an
honest sentence each, and a ranked list. That is the only instrument that found
any of these three problems, and none of them would have been guessed.

---

## 9. Reproducing it

```bash
python -m evals.w5_collect        # collect the 20 traces, needs an API key
python -m evals.w5_taxonomy       # rebuild the taxonomy, no API key needed
python test_acceptance.py         # 67 checks, no API key needed
```

`w5_collect` is resumable. Traces are appended to `w5_traces.jsonl` as they
complete, a re-run skips what is settled and retries only what errored, and calls
are spaced 4 seconds apart to stay under the free tier's per-minute cap.

The acceptance suite asserts the claims in this write-up directly:

- the pool is 60, every required string is verbatim, every requirement is
  satisfiable by a single chunk
- the draw is plain `random.sample` with seed 5, reproducible, and a different
  seed gives a different sample
- all 20 traces are complete, none left in the error state, none stale against
  the current corpus and prompt hash
- **every stored grade can be rebuilt from the trace alone**
- every trace has a hand-written note, and **no note names a group**
- every failing trace is in exactly one group, no passing trace is in any group
- the ranking really is frequency times severity, sorted
- every predicted metric says what would falsify it, and a guard metric exists

All 67 pass.

---

## 10. Files

| File | What it holds |
|---|---|
| [`w5_traces.md`](w5_traces.md) | The 20 traces, laid out to be read by a person |
| `w5_traces.json` | The same 20, machine-readable |
| `w5_traces.jsonl` | Append-only collection log, one line per attempt |
| [`w5_taxonomy.md`](w5_taxonomy.md) | Groups, ranking, target, prediction |
| [`../evals/w5_questions.py`](../evals/w5_questions.py) | The 60-question traffic pool |
| [`../evals/w5_sample.py`](../evals/w5_sample.py) | The draw |
| [`../evals/w5_trace.py`](../evals/w5_trace.py) | What a trace is, and the grading rule |
| [`../evals/w5_notes.py`](../evals/w5_notes.py) | The hand-written notes |
| [`../evals/w5_taxonomy.py`](../evals/w5_taxonomy.py) | The groups and the prediction |
| [Week 4 results](w4_results.md) | The retrieval work this builds on |
| [Week 3 results](results.md) | The chunking work that started it |
