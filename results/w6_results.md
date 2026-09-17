# Week 6 — Evaluation: assert what a rule can decide, judge only what it cannot

Week 5 read twenty traces by hand and named the top problem: the app refuses
questions the corpus can answer. Week 6 builds the machinery to measure that at
scale, changes one thing, and measures again.

The result: **46.5% to 79.1%** on the cases both runs scored, with false
refusals falling from 18 to 2. Retrieval was 0 misses in both runs, so the
answering chunk was already on screen every single time and nothing about search
explains the gain.

---

## 0. What this week produced

| | |
|---|---|
| 8 assertion checks, all deterministic | `evals/w6_checks.py` |
| 7 named failure modes | same |
| 60 cases, 6 regressions pinned to Week 5 traces | `evals/w6_cases.py` |
| An LLM judge for the two things a rule cannot decide | `evals/w6_judge.py` |
| A validation gate the judge did not pass | `evals/w6_validate_judge.py` |
| One command | `evals/run_evals.py` |
| The before and after | `results/w6_before_after.md` |

---

## 1. The number

Both runs cover the same 43 cases. The `after` run is not finished; section 7
says what that costs.

| Prompt | Passed | Rate |
|---|---|---|
| v1 (before) | 20/43 | 46.5% |
| **v2 (after)** | **34/43** | **79.1%** |

| Failure mode | v1 | v2 |
|---|---|---|
| `false_refusal` | 18 | **2** |
| `refusal_then_answer` | 10 | **4** |
| `unchecked_answer` | 4 | 3 |
| `wrong_source` | 4 | 4 |
| `retrieval_miss` | **0** | **0** |
| `missed_refusal` | **0** | **0** |

Nearly all of the gain is one mode. Everything else barely moved, which is what
a single-change measurement should look like.

By problem type, on the matched cases:

| Kind | v1 | v2 |
|---|---|---|
| policy | 2/6 | **6/6** |
| procedure | 2/4 | **4/4** |
| code_lookup | 9/16 | 13/16 |
| symptom | 2/7 | 4/7 |
| cross_article | 0/3 | 2/3 |
| noisy | 0/1 | 1/1 |
| multi_part | 2/3 | **1/3** |
| out_of_corpus | 2/2 | 2/2 |
| vague | 1/1 | 1/1 |

`policy` went from the worst kind to perfect. `multi_part` went down by one,
which is a single case on a set of three and is not a finding.

---

## 2. Eight rules, and the two things they cannot decide

Every check below is deterministic, binary, and free. No model is involved.

| Check | Catches |
|---|---|
| `not_refusal_then_answer` | Output that contradicts itself |
| `retrieval_put_answer_in_context` | Retrieval failure, separated from generation failure |
| `answered` | A refusal where an answer was possible |
| `has_resolvable_citation` | A claim nobody can check |
| `no_fabricated_citation` | An invented chunk_id |
| `cites_a_chunk_that_holds_the_answer` | A real citation that does not support the claim |
| `refused` | An answer where a refusal was required |
| `refusal_names_what_is_missing` | A refusal that says nothing useful |

`retrieval_put_answer_in_context` is the one that makes the rest work. It
separates "the search failed" from "the search worked and the model still got it
wrong", and it is why a false refusal can be detected without asking a judge.

Two things a rule genuinely cannot decide are left to a model:

- **Faithfulness.** A rule can confirm the cited chunk contains the required
  phrase. It cannot see that the answer *also* added a confident sentence the
  chunk never supported.
- **Relevancy.** An answer about ERR-4044 is fluent, cited and faithful, and
  useless if the agent asked about ERR-4032. Substring rules pass it.

---

## 3. The judge, and why it is not trusted

The judge is **binary, not 1 to 10**. A 1 to 10 scale hovers around 6 and 7 and
makes agreement with a human grader impossible to measure, because nobody can
say whether a 6 against a 7 is a disagreement.

It is shown **only the chunks the answer actually cited**, never the whole
retrieved context. Handing it everything would let an unsupported claim pass
because some other chunk happened to mention it.

Validation against 20 hand-graded cases:

| Dimension | Agreed | Agreement | Kappa | Trustworthy |
|---|---|---|---|---|
| faithful | 20/20 | 100% | 1.0 | yes |
| relevant | 19/20 | 95% | **n/a, no variance** | **no** |

**Verdict: DO NOT TRUST.**

The hand grading marked all 20 answers relevant. With no variance, Cohen's kappa
cannot be computed. 95% agreement on a dimension where the grader always said
yes proves nothing, so `cohens_kappa()` returns `None` rather than 1.0, and the
report says so.

**No judge number is quoted anywhere as a finding.** The assertion layer is
deterministic, needs no judge, and carries the whole result above. Shipping a
judge that was measured and refused is a better outcome than shipping one that
was never checked.

The grades were AI-drafted and that is recorded in
`results/w6_judge_grading_provenance.md` rather than left implicit.

---

## 4. The change: v1 to v2, two things and nothing else

### What a refusal may be about

**v1 rule 5:** *"A partial answer is a refusal."*

v1 never defined "partial". The model filled the gap and chose **shape** over
**facts**: asked to walk through a procedure when the corpus held a one-line
fix, it called the one line partial and refused. The fix was on screen.

**v2 rule 5:** *"Never refuse because of how the question is worded."* It then
names four traps:

- asks for steps, context gives a single instruction
- asks "can I", context states what to do instead
- expects a long procedure, context is one line
- uses different words for the same thing

And it defines the word v1 left open: an answer covering the substance in fewer
steps than expected **is a complete answer, not a partial one**.

**v2 rule 4** backs it: *"A refusal is about MISSING FACTS, and nothing else."*

### When the model decides

Fixing rule 5 alone was not enough. The model still wrote refusals and then
corrected itself in public, inside customer-facing answers:

> "Wait, let me re-read the context blocks."
> "I need to correct myself. The context does contain information about ERR-7215."
> "No wait, I need to follow the rules properly."

It was not failing to read the corpus. It reached for the refusal template as a
first draft, because the reply was the only place it could think.

So v2 adds a decision step **above** the rules: find the line that most directly
addresses the question, and let that settle it before writing a word. A table
row counts. A rule stated as "Never do X" counts as the answer to "can I do X".

**Rule 6 is new** and bans the self-correction itself, naming the exact phrases
the failures produced.

### What did not change

Rules 1 to 3 are **byte for byte identical** to v1, and the acceptance suite
asserts it. Citations, no outside knowledge, the fixed refusal string and the
ban on hedging all stay. The grounding cannot quietly widen while the refusal
rule loosens.

Nothing outside the prompt changed. Same corpus, chunker, embeddings, k, model
and temperature. `prompt_sha` is the only key that differs between the two runs.

---

## 5. The guard held

Loosening when the app may refuse could easily have made it answer things the
corpus cannot answer. That risk was written down in Week 5, before the fix
existed, and `missed_refusal` is tracked as a failure mode for exactly this
reason.

**`missed_refusal` is 0 in both runs.** Every question that should have been
refused was still refused.

All six pinned Week 5 regressions **held** in v2, against 2 of 6 under v1.

---

## 6. Measurement guards, each added after a near-miss

Every one of these exists because something nearly went wrong.

- **Config is pinned at first generation and never recomputed.** Reading live
  settings at report time once restamped a v1 run with v2's fingerprint. Each
  tag now carries its own `__config.json`.
- **`--compare` refuses a delta** when anything except `prompt_sha` differs
  between two runs, and refuses a partial run outright.
- **An incomplete run carries a banner** naming every case that did not run, so
  a partial total can never be read as a result.
- **Kappa returns `None` on zero variance** instead of 1.0, and forces
  `trustworthy=False`.
- **Every generation and every judgement is cached**, so a daily cap costs time
  and not work.

---

## 7. What this week does NOT tell you

- **The after run is 43 of 60.** Seventeen cases never generated against the
  free tier's daily cap: P07, P14, P24, P33, P34, P36, P40, P42, P44, P46, P48,
  P49, P50, P52, P53, P54, P58. Every number above is computed over the 43 cases
  **both** runs scored, so the two columns describe the same questions.
- **Four of the seven refusal guard cases are among the missing.** P51, P59 and
  P60 refused correctly. P52, P53, P54 and P58 have not run. The guard holds on
  3 of 7, not 7 of 7, and that is weaker evidence than it looks.
- **The generated `w6_before_after.md` borrows one denominator for both rows**,
  printing `34/60` where it means `34/43`. That file was written by hand from
  the two run files, with every figure checked back against them, and it says so
  at the top.
- **The judge is unvalidated**, so faithfulness and relevancy are unmeasured.
- **One model, one free tier.** `poolside/laguna-s-2.1:free` is a weak
  instruction-follower. Some of what v2 fixes is a weakness a stronger model
  would not have had.
- **`results/w6_archive/` holds a superseded run** on a draft prompt that no
  longer exists in the tree, fingerprint `6f7f9b1487018664`. It is kept rather
  than deleted because its numbers were reported while it was current.

---

## 8. Reproducing it

```bash
python -m evals.run_evals --tag before            # v1, set PROMPT_VERSION=v1
python -m evals.run_evals --tag after             # v2, set PROMPT_VERSION=v2
python -m evals.run_evals --compare before after
python -m evals.w6_validate_judge --sample 20     # writes the worksheet
python -m evals.w6_validate_judge --score         # grades the judge
python test_acceptance.py
```

`PROMPT_VERSION` in `.env` is the only switch. Both prompts live side by side in
`rag/answerer.py`, so the baseline can always be reproduced.

---

## 9. Files

| File | What it is |
|---|---|
| `evals/w6_checks.py` | The 8 rules and 7 failure modes |
| `evals/w6_cases.py` | 60 cases, 6 regressions pinned by banned mode |
| `evals/w6_judge.py` | The binary judge |
| `evals/w6_validate_judge.py` | The gate the judge did not pass |
| `evals/run_evals.py` | The one command |
| `rag/answerer.py` | Both prompts, v1 at line 40, v2 at line 108 |
| `results/w6_before_after.md` | The comparison |
| `results/w6_run_before.md` | v1, all 60 cases |
| `results/w6_run_after.md` | v2, 43 of 60 |
| `results/w6_judge_validation.md` | Why the judge is not trusted |

---

## 10. The one-line answer to the week's question

A rule you can write down should never be handed to a judge, and a judge you
have not measured against a human should never be quoted at all.
