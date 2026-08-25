# Week 4 — Debugging Retrieval: failure separation and one change

**Headline:** hit-rate@3 went from **28/30 to 30/30** with exactly one change,
adding a BM25 keyword arm fused into the existing vector search. hit@1 went from
25/30 to 29/30. Nothing regressed.

> **Note on the corpus.** The 6 articles were written for this exercise. The
> billing system, the error codes and the dates are invented. Nothing here
> documents a real product.

---

## 0. What changed, and what did not

Exactly one thing changed. The mentor checklist asks for one, not five.

| | Before | After |
|---|---|---|
| Retrieval | vector search alone | vector search **fused with BM25 by RRF** |
| Corpus | the same 6 articles | unchanged |
| Chunker | structure-aware (what Week 3 shipped) | unchanged |
| Embedding model | `BAAI/bge-small-en-v1.5` | unchanged |
| Collection | `hc_structured` | unchanged |
| k | 3 | unchanged |
| Hit rule | article match + literal answer text | unchanged |

The change is a single flag, `retrieval_mode`, dispatched in
[`rag/hybrid.py`](../rag/hybrid.py). Nobody has to take my word for what moved.

No parameter was tuned. RRF uses the conventional constant 60. BM25 uses the
standard k1 = 1.5 and b = 0.75. Tuning them would have been a second change
smuggled in as one.

**No reranker, no query rewriting, no HyDE, no MMR.** All were on the syllabus
and all were deliberately left out. Adding them would make the number
unattributable.

---

## 1. Why this change, and not a smarter model

Week 3 ended with a diagnosis, not a guess. Two retrieval failures were
documented there with the same root cause:

> Dense vectors match the *shape* of an error-code table, not the literal token
> `ERR-7208`. Every error table in the corpus is three columns of codes, causes
> and fixes, so they are near-duplicates as vectors, and one rare token cannot
> separate them.

That is a **retrieval** failure. A smarter or more expensive language model
changes nothing, because the answering chunk never reaches the model at all.

BM25 has the opposite bias. A term appearing in one chunk out of 34 earns a large
IDF, so an exact code dominates the ranking. Measured on this corpus:

| token | IDF |
|---|---|
| `err-7208` | 3.150 |
| `the` | 0.105 |

The tokeniser is the whole trick. A naive one splits `ERR-7208` into `err` and
`7208`, and `err` appears in nearly every chunk, so the signal vanishes.
[`rag/keyword.py`](../rag/keyword.py) keeps `err-7208` whole **and** emits the
parts, so the rare form dominates while "ERR 7208" with a space still matches.

---

## 2. The question set

The Week 3 set could not be used. All 8 of its questions pass, at k=5 and at
k=3, on both chunkers. **A set with no failures cannot be used to study
failures.**

So a new set covers every code in the corpus: 25 `ERR` codes and 5 `MIG` codes,
30 in total. Every answer was copied out of an article table, so every question
has a known-correct location.

- Written before the hybrid retriever existed, same discipline as Week 3.
- Every `must_contain` string is verbatim from the corpus. The acceptance test
  asserts this, so a typo cannot silently create a fake failure.
- One question per code, no duplicates.

Full set: [`evals/w4_questions.py`](../evals/w4_questions.py).

### The hit rule, unchanged from Week 3

A question is a hit at k when one of the top k chunks has the expected
`article_id` **and** literally contains every `must_contain` string.

`must_contain` is always the code plus one phrase unique to that row's fix. A
chunk holding `ERR-4032` but not its fix cannot answer the question, so it does
not count.

---

## 3. The number

| | hit-rate@3 | hit@1 | MRR | answer never in top-10 |
|---|---|---|---|---|
| **before** — dense | **28/30** | 25/30 | 0.8889 | 0 |
| **after** — hybrid | **30/30** | 29/30 | 0.9778 | 0 |
| change | **+2** | **+4** | **+0.0889** | 0 |

- **Fixed (2):** W7 `ERR-4021`, W15 `ERR-5108`
- **Broke (0):** none
- **Still failing at k=3 (0):** none

Per-question record and full search dump:
[`w4_hitrate.md`](w4_hitrate.md), [`w4_search_dump.md`](w4_search_dump.md).

### How the fix actually worked

Five questions had the answering chunk promoted. In every case BM25 ranked the
exact code far higher than the vector arm did, and RRF carried it up.

| Q | code | dense rank | BM25 rank | fused rank |
|---|---|---|---|---|
| W7 | `ERR-4021` | 4 | 2 | **3** |
| W8 | `ERR-4032` | 3 | 1 | **1** |
| W15 | `ERR-5108` | 4 | 1 | **1** |
| W16 | `ERR-5114` | 3 | 1 | **1** |
| W17 | `ERR-5127` | 2 | 1 | **1** |

Only W7 and W15 cross the k=3 line, so only they move the headline number. W8,
W16 and W17 were already inside the window and simply got more reliable, which
is what the MRR gain measures.

Note the pattern. The vector arm consistently parked the right chunk at rank 3
or 4, just outside or barely inside a k=3 window. That is the signature of the
Week 3 diagnosis: it knows the right *kind* of table and cannot pick the right
*row group*.

---

## 4. What the change did NOT fix

The checklist asks this directly, and it is the more useful half.

**Still not rank 1: W7 `ERR-4021`.** BM25 puts it second, not first, and fusion
lands it at 3. The query says "ERR-4021" but the row's distinguishing words are
"metered usage record" and "Rebuild Usage", which appear in neighbouring rows
too. Neither arm is confident. A cross-encoder reranker is the natural next
change, and it would be measured on its own.

**Bucket B failures are untouched by design.** Where retrieval already put the
right chunk in front of the model and the answer was still wrong, hybrid search
cannot help. Fixing those means changing the prompt or the model, which is a
different experiment.

**The corpus is small.** 34 chunks, so top-3 is roughly 9% of the index. BM25
looks strong partly because rare codes are genuinely rare here. On a corpus of
thousands of articles, more codes collide and the gain would shrink. This number
is honest but it is not a promise about scale.

---

## 5. Failure separation: the two kinds of wrong

"Wrong sometimes" is useless to fix. Two kinds of wrong need opposite fixes.

| Bucket | Meaning | Fix |
|---|---|---|
| **A — wrong document fetched** | The answering chunk is not in the top-3. The model never saw the answer. | Fix retrieval. A smarter model changes nothing. |
| **B — right document, wrong answer** | The answering chunk **is** in the top-3 and the answer is still wrong or refused. | Fix the prompt, the context layout, or the model. |

Both are decided mechanically, no judgement calls:

- `retrieval_ok` — one of the top-3 chunks passes the hit rule.
- `answer_ok` — the model did not refuse, **and** at least one chunk_id it cited
  resolves to a chunk that passes the same rule.
- Label: not `retrieval_ok` → **A**. `retrieval_ok` and not `answer_ok` → **B**.
  Otherwise pass.

The `answer_ok` rule catches the nastiest case: a fluent answer citing the
neighbouring table row.

Rule and code: [`evals/w4_failures.py`](../evals/w4_failures.py).

### Results: complete, 60 of 60 labelled

| mode | pass | A: wrong document | B: right document, wrong answer |
|---|---|---|---|
| **before** — dense | 22/30 | **2** | 6 |
| **after** — hybrid | 23/30 | **0** | 7 |

**Bucket A went from 2 to 0.** The change emptied the retrieval-failure bucket
entirely. The two A cases were **W7 (`ERR-4021`)** and **W15 (`ERR-5108`)** —
exactly the two questions the search-only measurement in section 3 said were
fixed. Two independent measurements, one built on retrieval alone and one on
generated answers, agree on the same two questions. That is the consistency
check worth having.

**Bucket B did not shrink, and was never going to.** Where retrieval already put
the right chunk in front of the model and the answer was still wrong, a keyword
arm cannot help. Fixing those means changing the prompt or the model, which is a
separate experiment. This is the honest answer to "which failures did your change
NOT fix".

### Two caveats on these numbers

**The model changed.** The OpenRouter balance ran out mid-project, so labelling
was completed on `poolside/laguna-s-2.1:free` rather than
`google/gemini-2.5-flash`. The free model was validated first against the Week 3
set: 3 cited answers with resolving citations and 3 forced refusals, all six
correct.

This matters differently for the two buckets:

- **Bucket A is model-independent.** It is decided purely by whether retrieval
  put the answering chunk in the top-3. The 2 to 0 result would be identical on
  any model.
- **Bucket B is model-dependent.** Both modes here were labelled with the same
  model, so the dense-to-hybrid comparison is valid. Comparing these B counts to
  anything produced with `gemini-2.5-flash` is not.

**B membership moves between runs.** Three questions are in B under both modes
(W13, W14, W20). The rest differ. That churn points to variance in a smaller
model rather than an effect of the change, and it is a reason not to read too
much into a single B count.

## 6. The inspection view

Two forms, both showing question, what was fetched, and the final answer
together.

**As a file:** [`w4_inspect.md`](w4_inspect.md), one row per question, with `>`
marking the chunk that actually holds the answer. When the fetched column has no
marked chunk, the answer column was never going to be right. That is the whole
diagnostic in one glance.

**Interactively:** [`ask.py`](../ask.py) prints the answer, a pass/fail line per
citation, and the retrieved chunks with `<<< USED IN ANSWER` on the one the
answer came from. Week 4 adds a `:mode` command, so the same question can be run
through both retrieval modes back to back:

```
> :mode dense
> A renewal failed with ERR-5108. What should the agent ask the customer to do?
> :mode hybrid
> A renewal failed with ERR-5108. What should the agent ask the customer to do?
```

Chunks that only the keyword arm found are tagged `[BM25 ONLY]`.

---

## 7. Reproducing it

```bash
python -m evals.w4_measure      # the before/after number, no API key needed
python -m evals.w4_failures     # the failure labels, needs credits
python test_acceptance.py       # 32 checks, no API key needed
```

The acceptance suite asserts the claims in section 3 directly:

- the BM25 tokeniser keeps `err-7208` as one token
- BM25 alone ranks the `ERR-7208` chunk first
- a rare code outweighs a common word on IDF
- hybrid strictly improves hit-rate@3
- hybrid breaks nothing dense already found
- both modes share one embedding model, and RRF and BM25 use untuned defaults
- every `must_contain` string is verbatim in the corpus

All 32 pass.

---

## 8. Files

| File | What it holds |
|---|---|
| [`w4_hitrate.md`](w4_hitrate.md) | The before/after number and the per-question record |
| [`w4_search_dump.md`](w4_search_dump.md) | Top-10 for all 30 questions, both modes, with per-arm ranks |
| [`w4_failures.md`](w4_failures.md) | Bucket labels and evidence. Incomplete, see section 5 |
| [`w4_inspect.md`](w4_inspect.md) | Question, fetched, answer, side by side |
| `w4_measure.json`, `w4_failures.json` | Machine-readable runs |
| [Week 3 results](results.md) | The chunking work this builds on |
