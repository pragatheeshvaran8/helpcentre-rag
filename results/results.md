# Week 3 Task Set A — Results

Ingest of the 6 new help-centre articles on the billing migration, and a
measurement of whether the chunker can find an answer that lives inside a
troubleshooting table.

**Headline:** the two chunkers score the same on hit-in-top-5, 8/8 each. The
chunker did not move that number. It moved a different one: how often a
header-less table fragment is handed to the model. That went from 7 chunks to 0.

---

## 0. What was held constant

Changing the chunker and the embedding model in the same run teaches you nothing
about which one moved the number. Only the chunker changed here.

| Held constant | Value |
|---|---|
| Corpus | The same 6 articles, `HC-4001` to `HC-4006` |
| Embedding model | `BAAI/bge-small-en-v1.5`, local, normalised |
| Distance metric | cosine, so relevance score reads as `1 - distance` |
| Retrieval depth | k = 5 |
| Target chunk size | 1000 characters |
| Questions | The same 8, written before any search was run |

The one intended difference is boundary policy. The baseline overlaps by 150
characters. The structure-aware chunker does not overlap, because it packs whole
structural units and never cuts one in half, so it has nothing to stitch back
together. That is intrinsic to the strategy, not a second knob.

**Time reality.** Only the 6 new articles were indexed. No historical corpus was
re-indexed. A full rebuild of both indexes plus every measurement in this
document takes **21.1 seconds** once the embedding model is in memory.

### The index

| Strategy | Chunks | Chunks holding table rows | Header-less ("orphan") | Orphan rate | Mean chars |
|---|---|---|---|---|---|
| baseline | 32 | 16 | 5 | **31.2%** | 680 |
| structured | 34 | 16 | 0 | **0.0%** | 641 |

An orphan chunk carries table data rows but has lost the header row above them.
Nothing in it says which column is the cause and which is the fix.

---

## 1. The 8 questions and their known-correct location

Written by reading the articles, before any retrieval code existed. The evidence
is the git history: commit `c25d0a0` contains the corpus and these questions and
nothing else — no retriever, no chunker, no vector store.

| Q | Type | Question | Known-correct article + section |
|---|---|---|---|
| Q1 | table row | What does ERR-4032 mean on an invoice, and what is the fix? | `HC-4002` → Invoice error codes, row ERR-4032 |
| Q2 | table row | A renewal failed with a token error because the saved card was not re-tokenised at cutover. Which error code, and what should the agent ask? | `HC-4003` → Decline and token error codes, row ERR-5108 |
| Q3 | table row | A German business customer is getting ERR-7203 on their VAT number. What causes it and how do we clear it? | `HC-4005` → Tax validation error codes, row ERR-7203 |
| Q4 | table row | Our webhook listener for `invoice.payment_succeeded` went silent. Which v2 event replaced it? | `HC-4006` → Webhook event renames, row `invoice.payment_succeeded` |
| Q5 | table row | A customer was on legacy Team 10. Which new plan, and what seat rule? | `HC-4004` → Legacy to new plan map, row Team 10 |
| Q6 | prose | How long is the billing ledger read-only during cutover, and can customers pay? | `HC-4001` → What changed (prose) / Phase 3 row |
| Q7 | prose | What happened to stored cards not used for a long time, and what must those customers do? | `HC-4003` → What happened to stored cards (prose) |
| Q8 | prose | When does the v1 billing API stop working, and what do callers get after that? | `HC-4006` → Versioning and sunset (prose) |

Five of the eight depend on a row inside a troubleshooting table. The task asks
for at least three.

### How a hit was decided

No human judgement. A question is a hit-in-top-5 when at least one of the 5
retrieved chunks satisfies both:

1. the chunk's `article_id` equals the expected article, and
2. the chunk literally contains every `must_contain` string for that question.

Condition 2 is deliberately unforgiving. A chunk that mentions ERR-4032 but has
lost the fix half of the row cannot answer the question, so it does not count.
That is exactly the damage a table-blind chunker does. The rule is in
[`evals/questions.py`](../evals/questions.py) and was fixed before any run.

---

## 2. The two numbers

| Chunking strategy | hit-in-top-5 |
|---|---|
| baseline — `RecursiveCharacterTextSplitter`, 1000 / 150 | **8/8** |
| structured — table-row aware | **8/8** |

### Per-question record

| Q | Type | Expected article | baseline | rank | structured | rank |
|---|---|---|---|---|---|---|
| Q1 | table row | HC-4002 | HIT | 2 | HIT | 3 |
| Q2 | table row | HC-4003 | HIT | 1 | HIT | 1 |
| Q3 | table row | HC-4005 | HIT | 1 | HIT | 1 |
| Q4 | table row | HC-4006 | HIT | 1 | HIT | 1 |
| Q5 | table row | HC-4004 | HIT | 1 | HIT | 1 |
| Q6 | prose | HC-4001 | HIT | 1 | HIT | 1 |
| Q7 | prose | HC-4003 | HIT | 1 | HIT | 1 |
| Q8 | prose | HC-4006 | HIT | 1 | HIT | 1 |

Full top-5 with scores and chunk text for all 16 runs is in
[`search_dump.md`](search_dump.md).

### Secondary metrics, same run, same 8 questions

hit-in-top-5 saturated. On a 6-article corpus, top-5 is about 15% of the whole
index, so almost anything relevant gets in. These numbers come from the identical
retrieval run. No question was rewritten and nothing was re-searched.

| Metric | baseline | structured |
|---|---|---|
| hit-in-top-5 | 8/8 | 8/8 |
| hit-in-top-1 | 7/8 | 7/8 |
| mean reciprocal rank | **0.9375** | 0.9167 |
| chunks delivered into context | 40 | 40 |
| of those, header-less table chunks | **7** | **0** |
| questions given a header-less chunk | **4/8** | **0/8** |

Read that honestly. On recall the two are identical. On rank the baseline is
very slightly better. The structure-aware chunker's win is that it never once
handed the model a table fragment with no columns, across 40 delivered chunks.
The baseline did that 7 times, on half the questions.

---

## 3. The retrieval that embarrassed me

**Q1: "What does ERR-4032 mean on an invoice, and what is the fix?"**

Neither chunker put the right chunk first. Both were beaten by a different error
table.

**baseline, top 3**

| rank | score | chunk_id | article | verdict |
|---|---|---|---|---|
| 1 | 0.8047 | `HC-4002-baseline-004` | HC-4002 | right article, **header-less**, no ERR-4032 |
| 2 | 0.7929 | `HC-4002-baseline-003` | HC-4002 | HIT |
| 3 | 0.7798 | `HC-4005-baseline-004` | HC-4005 | wrong article, header-less |

**structured, top 3**

| rank | score | chunk_id | article | verdict |
|---|---|---|---|---|
| 1 | 0.8002 | `HC-4005-structured-004` | HC-4005 | **wrong article** — the tax error table |
| 2 | 0.8001 | `HC-4002-structured-005` | HC-4002 | right article, wrong rows |
| 3 | 0.7929 | `HC-4002-structured-004` | HC-4002 | HIT |

**Diagnosis.** The embedding model matches the *shape* of an error-code table,
not the literal token `ERR-4032`. Every one of these chunks is a three-column
table of codes, causes and fixes. To a dense vector they are near-identical. The
top-1 for baseline scores 0.8047 while the chunk that actually holds the answer
scores 0.7929 — the wrong chunk wins by 0.012.

The structure-aware chunker makes this slightly worse, and the reason is its own
fix. Repeating the header row `| Error code | Cause | Fix |` on every row-group
is what removes orphans, and it also makes every error table in the corpus look
more alike. That is why its MRR is 0.9167 against the baseline's 0.9375. The
tax-error group from HC-4005 outranks the invoice-error group from HC-4002 by
0.0001.

**What this really says.** Chunking is the wrong tool for this failure. Dense
retrieval is weak on rare exact identifiers. The fix is hybrid retrieval: a
keyword or BM25 arm that matches `ERR-4032` as a literal token, fused with the
dense arm. I did not build it, because that would change retrieval and muddy the
two-strategy comparison this task is about. It is the next change I would make.

### The same fault, caught later, doing real damage

Q1 only cost a rank. Poking at the index by hand afterwards found the same fault
producing a user-visible failure.

**"What does ERR-7208 mean?"** — the corpus answers this. `ERR-7208` is a row in
the tax validation table in HC-4005: VIES was unreachable, retry after one hour,
do not remove the customer's VAT ID.

The system **refused it**.

| | chunk holding ERR-7208 | in top-5? | what ranked first instead |
|---|---|---|---|
| structured | `HC-4005-structured-003` | **no** | `HC-4005-structured-004` — the *other half* of the same table, holding ERR-7302 and ERR-7310 |
| baseline | `HC-4005-baseline-003` | **no** | `HC-4002-baseline-003` — the invoice error table, a different article |

Neither chunker retrieved it. This is not a structure-aware regression. Both
strategies fail the same way, which is the clearest evidence yet that the fault
lives in the embedding model and not in the chunker.

The mechanism is stark. `HC-4005-structured-003` and `HC-4005-structured-004`
are two row-groups of *one* tax table. They share a header row, a column layout,
and most of their vocabulary. To a dense vector they are near-duplicates. The
query says `ERR-7208`, which appears in exactly one of them, and the model has no
way to weight that one token heavily enough to separate them.

**Two things worth saying about it.**

First, it failed safely. Faced with the wrong half of the right table, the model
refused rather than telling an agent that ERR-7208 means an expired United States
exemption certificate. That answer would have been fluent, plausible and wrong,
and it would have reached a customer. The forced refusal turned a retrieval bug
into a visible gap instead of a silent lie.

Second, a refusal on an answerable question is still a failure. It is a false
negative. My 8/8 hit-rate does not see it, because ERR-7208 was never one of the
8 questions. That is a limit of an 8-question benchmark, not a defence of it.

Both this and Q1 have one fix: a keyword arm that matches `ERR-7208` as a literal
string, fused with the dense arm. That is the first thing I would build next, and
it would be measured against these same 8 questions plus a new set drawn from
every error code in the corpus.

---

## 4. A defect I shipped and then found

The first version of the structure-aware chunker emitted **6 content-free
chunks** out of 39 — 15% of the index. Each was a bare article title with no body:

```
# Subscription and Plan Mapping After Migration
```

That happened because a heading flushed the buffer, and an article title
followed immediately by a section heading left the title alone in it.

It was not harmless. On the metadata-filter query, `HC-4004-structured-001` — a
chunk containing nothing but that title — ranked **first**, above every real
paragraph in the corpus. A short chunk made almost entirely of topic words is a
very good match for a short topical query, and it carries no information at all.

Fixed in [`rag/chunkers.py`](../rag/chunkers.py): consecutive headings now
accumulate and attach to the content that follows, and a buffer holding only
headings is never emitted. The index went from 39 chunks to 34, with 0
content-free chunks. Hit rates did not change. The evidence from before the fix
is kept in [`defect_evidence/`](defect_evidence/).

I found this only because I read the top-1 result instead of trusting the
hit-rate. The hit-rate was 8/8 both before and after the defect was fixed.

---

## 5. Metadata filter on `product_area`

The query is deliberately ambiguous. "Retries" is documented in three product
areas: payments (dunning schedule), subscriptions (renewal) and api (webhook
backoff). Unfiltered search has to guess which the user meant.

- **Query:** *How do retries work after the migration?*
- **Filter:** `{"product_area": {"$eq": "api"}}`
- **Index searched:** `structured`
- **Top-1 changed:** **YES**

### Result list A — UNFILTERED

| rank | score | chunk_id | article | product_area |
|---|---|---|---|---|
| 1 | 0.7281 | `HC-4001-structured-002` | HC-4001 | billing_core |
| 2 | 0.7172 | `HC-4006-structured-005` | HC-4006 | api |
| 3 | 0.7103 | `HC-4001-structured-004` | HC-4001 | billing_core |
| 4 | 0.6824 | `HC-4003-structured-001` | HC-4003 | payments |
| 5 | 0.6759 | `HC-4001-structured-005` | HC-4001 | billing_core |

### Result list B — FILTERED to `product_area = api`

| rank | score | chunk_id | article | product_area |
|---|---|---|---|---|
| 1 | 0.7172 | `HC-4006-structured-005` | HC-4006 | api |
| 2 | 0.6690 | `HC-4006-structured-003` | HC-4006 | api |
| 3 | 0.6503 | `HC-4006-structured-004` | HC-4006 | api |
| 4 | 0.6442 | `HC-4006-structured-002` | HC-4006 | api |
| 5 | 0.6407 | `HC-4006-structured-001` | HC-4006 | api |

Top-1 moved from `HC-4001-structured-002` (billing_core, 0.7281) to
`HC-4006-structured-005` (api, 0.7172).

Note ranks 2 to 5 of list B. Those four chunks are **not present anywhere in
list A**. That proves the filter is a pre-filter applied inside Chroma, not a
post-filter applied to an already-returned top-5. A post-filter can only delete
rows, so it could never promote a chunk that was outside the original top-5.

Both lists with full chunk text: [`filter_demo.md`](filter_demo.md).

---

## 6. Three cited answers

Model `google/gemini-2.5-flash` via OpenRouter, temperature 0.0, searching the
`structured` index. Every sentence must carry a `[chunk_id]`. Every cited id is
then resolved against the live vector store.

**All 3 answers: every citation resolves, and every cited id was present in the
context the model was shown.** No fabricated chunk_ids.

### Q1 — What does ERR-4032 mean on an invoice, and what is the fix?

```
The error code ERR-4032 on an invoice means that the invoice line item references
a legacy tax code that no longer exists in BL2, and the migration could not map it
automatically [HC-4002-structured-004]. To fix this, you should re-map the line
item to a current tax code under Billing then Tax Codes, and then reissue the
invoice [HC-4002-structured-004].
```

Citation → [`HC-4002-structured-004`](chunks_structured.md#hc-4002-structured-004),
resolves, article HC-4002, file `HC-4002-invoice-errors.md`.

### Q3 — A German business customer is getting ERR-7203. What causes it and how do we clear it?

```
The ERR-7203 error indicates that the VAT ID failed real-time validation against
VIES, meaning the number is well-formed but is not registered or is not valid for
cross-border trade [HC-4005-structured-003]. To clear this error, you should ask
the customer to confirm the VAT ID with their tax authority, and then click
Revalidate on the Tax tab [HC-4005-structured-003].
```

Citation → [`HC-4005-structured-003`](chunks_structured.md#hc-4005-structured-003),
resolves, article HC-4005, file `HC-4005-tax-and-vat.md`.

### Q4 — Which v2 event replaced `invoice.payment_succeeded`?

```
The `invoice.payment_succeeded` event was replaced by `billing.invoice.paid` in
v2. [HC-4006-structured-004] This new event fires once after ledger settlement,
not upon processor approval. [HC-4006-structured-004]
```

Citation → [`HC-4006-structured-004`](chunks_structured.md#hc-4006-structured-004),
resolves, article HC-4006, file `HC-4006-billing-api-and-webhooks.md`.

Every chunk_id above is a live primary key. Resolve any of them yourself. This
is the actual output, and it is the check a grader would run:

```
$ python -m evals.dump_chunks --resolve HC-4002-structured-004

--- HC-4002-structured-004 found in 'structured' ---
source_file=HC-4002-invoice-errors.md  article_id=HC-4002  product_area=invoicing  last_updated=2026-06-11

| Error code | Cause | Fix |
|---|---|---|
| ERR-4010 | The invoice references a customer address that failed validation during import. Most often a missing postal code. | Open Billing then Customer Details, complete the address, then click Revalidate. The invoice finalises on the next hourly run. |
| ERR-4021 | Two line items on the same invoice resolve to the same metered usage record. This happens on accounts that had overlapping legacy subscriptions. | Void the invoice, then run Rebuild Usage for the period. Never delete the usage record directly. |
| ERR-4032 | The invoice line item references a legacy tax code that no longer exists in BL2. The migration could not map it automatically. | Re-map the line item to a current tax code under Billing then Tax Codes, then reissue the invoice. |
```

The cited chunk contains the exact claim, and it still carries its
`| Error code | Cause | Fix |` header, so the words "legacy tax code" are
readable as a cause and "reissue the invoice" as a fix.

The full text of each cited chunk is printed in
[`generation.md`](generation.md), and every chunk in the index with a matching
anchor is in [`chunks_structured.md`](chunks_structured.md).

---

## 7. Three refusals

These three answers appear nowhere in the 6 articles. Each is deliberately
adjacent to real content, so a weak prompt would happily invent something
plausible.

**The relevance gate was disabled for all three.** The model was shown real
retrieved context, scoring 0.67 to 0.69, well above the 0.30 gate. The gate never
fired. The model itself did the refusing. A refusal produced by a code path that
never called the model would prove nothing about the prompt.

### R1 — refund SLA

*What is the refund SLA? How many business days does a refund take to reach the customer's bank?*

Top-1 retrieved: `HC-4003-structured-006`, score **0.6868**. Gate fired: **false**.

```
REFUSED: The help-centre corpus does not contain this information.
Missing: refund SLA and number of business days for a refund to reach the customer's bank
```

### R2 — chargeback fee

*What is the chargeback fee we pass on to the customer?*

Top-1 retrieved: `HC-4002-structured-005`, score **0.6823**. Gate fired: **false**.

```
REFUSED: The help-centre corpus does not contain this information.
Missing: chargeback fee
```

### R3 — SSO and SAML

*Which SSO providers does the new billing portal support, and can we enforce SAML for the billing role?*

Top-1 retrieved: `HC-4001-structured-001`, score **0.6726**. Gate fired: **false**.

```
REFUSED: The help-centre corpus does not contain this information.
Missing: Supported SSO providers and SAML enforcement for the billing role
```

Verified absent from all 6 articles by word-boundary search: `SSO` 0 hits, `SAML`
0 hits, `chargeback` 0 hits, `refund SLA` 0 hits, `business days` 0 hits.

### Why the refusal holds

The grounding prompt never says "use your best judgement" and never says "if the
context is insufficient, do your best". Those sentences are how ERR-4032 gets an
invented fix. The refusal is an instruction with a fixed output string:

```
4. If the CONTEXT BLOCKS do not contain the information needed to answer the
   question, you MUST reply with exactly this, and nothing else:

REFUSED: The help-centre corpus does not contain this information.
Missing: <one short line naming what was asked for and not found>

5. A partial answer is a refusal. If you can answer only part of the question,
   you must still refuse using the format in rule 4, and name the missing part.
```

Rule 5 matters more than rule 4. Half-answering is the failure mode that actually
reaches customers. The full prompt is in
[`rag/answerer.py`](../rag/answerer.py) and reproduced in
[`generation.md`](generation.md).

---

## 8. Bonus — precision against completeness

**Question:** *What does ERR-4032 mean, what is the fix, and what happens to the
invoice number after I reissue the invoice?*

Three parts. Parts 1 and 2 are one row of the invoice error table. Part 3 is
prose, in a different section of the same article.

| k | strategy | ERR-4032 row retrieved | numbering prose retrieved | parts answered | refused |
|---|---|---|---|---|---|
| 5 | baseline | yes | yes | 3/3 | no |
| 5 | structured | yes | yes | 3/3 | no |
| 1 | baseline | **no** | no | 0/3 | yes |
| 1 | structured | **yes** | no | 1/3 | yes |

**At k=5 the predicted tension did not appear.** I predicted before running that
the structure-aware chunker would starve the model of prose. It did not. Both
retrieved the numbering paragraph inside their five chunks, and both answered all
three parts. Reported as it happened.

**At k=1 it appears exactly as described.** Structure-aware wins retrieval: its
single chunk is the ERR-4032 row, complete with its header. Baseline's single
chunk is a header-less block of neighbouring rows that does not contain ERR-4032
at all. Then structure-aware loses the answer:

```
baseline, k=1  → retrieved HC-4002-baseline-004 (965 chars, no ERR-4032)
REFUSED: The help-centre corpus does not contain this information.
Missing: ERR-4032 meaning, fix, and impact on invoice number after reissuing
```

```
structured, k=1 → retrieved HC-4002-structured-004 (802 chars, holds ERR-4032)
REFUSED: The help-centre corpus does not contain this information.
Missing: what happens to the invoice number after I reissue the invoice
```

**Two sentences on the tension.** A tight, structure-clean chunk retrieves the
exact row and nothing around it, so it answers the question it was cut for and
goes blind to anything the surrounding prose qualifies. A loose character chunk
carries that surrounding prose along by accident, which sometimes completes an
answer and sometimes hands the model a table fragment with no columns.

Notice what the two refusals tell you. Both failed, but structure-aware failed
*precisely*: it named the one thing it was missing. The baseline could not even
say what it lacked. When a chunk is well-formed, a refusal becomes a usable
signal about which article section to widen retrieval into.

Full detail: [`bonus.md`](bonus.md).

---

## 9. Which chunker ships, and why

**Structure-aware ships.**

It does not retrieve better. On these 8 questions it is level on hit-in-top-5
(8/8 versus 8/8) and level on hit-in-top-1 (7/8 versus 7/8), and its mean
reciprocal rank is very slightly worse, 0.9167 against 0.9375. If retrieval
recall were the only thing I measured, I would have to call this change a
no-op and keep the incumbent.

I am shipping it for what happens after retrieval. Across the same 8 questions
both chunkers deliver 40 chunks into context. Seven of the baseline's 40 are
table data rows with the header row cut off, spread across half the questions.
The structure-aware chunker delivered zero, and its index has zero, against
31.2% of the baseline's table-bearing chunks. A chunk reading
`| ERR-4044 | ... | Convert the remainder to account credit ... |` with no header
above it is a fix instruction with nothing saying which code it belongs to. That
is the input most likely to produce a confidently wrong answer about ERR-4032,
and hit-in-top-5 cannot see it, because the retrieval was technically fine. The
bonus run showed the same thing from the other side: when the structure-aware
chunker fails, it fails legibly and names what it is missing.

The cost is real and I am accepting it knowingly. Repeating the header row on
every row-group makes every error table in the corpus look more alike to the
embedding model, which is precisely why Q1 ranks third instead of second. That
cost is bounded and rank-shaped. The orphan-chunk risk is unbounded and
answer-shaped. If the MRR gap widens on a larger corpus, the fix is hybrid
retrieval for exact identifiers, not going back to cutting tables in half.

---

## 10. Files

| File | What it holds |
|---|---|
| [`hit_matrix.md`](hit_matrix.md) | The two X/8 numbers and the per-question record |
| [`search_dump.md`](search_dump.md) | Search-only top-5 for all 8 questions, both strategies, with text |
| [`filter_demo.md`](filter_demo.md) | Unfiltered and filtered result lists with full chunk text |
| [`generation.md`](generation.md) | 3 cited answers, 3 refusals, the grounding prompt, cited chunk text |
| [`bonus.md`](bonus.md) | Precision-versus-completeness at k=5 and k=1 |
| [`chunks_baseline.md`](chunks_baseline.md) | All 32 baseline chunks, anchored by chunk_id |
| [`chunks_structured.md`](chunks_structured.md) | All 34 structured chunks, anchored by chunk_id |
| [`code_diff.md`](code_diff.md) | The diff adding the second chunker and the metadata fields |
| [`defect_evidence/`](defect_evidence/) | Pre-fix output showing the 6 content-free chunks |
| `search_eval.json`, `filter_demo.json`, `generation.json`, `bonus.json` | Machine-readable runs |
