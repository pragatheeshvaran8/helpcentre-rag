# Week 6 eval run: `after`

> **INCOMPLETE RUN. 17 of 60 cases never ran.**
> Generation failed for them, so they are absent from every number
> below. The percentages are over the cases that DID run, not over
> the eval set. This is not a result yet.

> Not run: P07, P14, P24, P33, P34, P36, P40, P42, P44, P46, P48, P49, P50, P52, P53, P54, P58

> Re-run `python -m evals.run_evals --tag after` to fill them in. Completed cases are cached and
> are not charged again.

- Cases scored: 43 of 60
- Passed every applicable assertion: **34/43** (79.1%)
- Mean assertion score: 0.9333

## Run fingerprint

| Setting | Value |
|---|---|
| strategy | `structured` |
| retrieval_mode | `hybrid` |
| k | `3` |
| embedding_model | `BAAI/bge-small-en-v1.5` |
| chunk_count | `34` |
| corpus_sha | `b5eed06a26dba4e3` |
| llm_model | `poolside/laguna-s-2.1:free` |
| llm_temperature | `0.0` |
| prompt_sha | `4a4b6fc6a1a4e1af` |

## Pass rate by problem type

| Kind | Passed | Rate |
|---|---|---|
| code_lookup | 13/16 | 81% |
| cross_article | 2/3 | 67% |
| multi_part | 1/3 | 33% |
| noisy | 1/1 | 100% |
| out_of_corpus | 2/2 | 100% |
| policy | 6/6 | 100% |
| procedure | 4/4 | 100% |
| symptom | 4/7 | 57% |
| vague | 1/1 | 100% |

## Failure modes

| Mode | Count |
|---|---|
| retrieval_miss | 0 |
| false_refusal | 2 |
| unchecked_answer | 3 |
| fabricated_citation | 0 |
| wrong_source | 4 |
| refusal_then_answer | 4 |
| missed_refusal | 0 |

## Regressions from Week 5

- Pinned: 4
- Held: 4
- Recurred: none
- Broke a new way: none

## Failing cases

| Case | Kind | Failure modes |
|---|---|---|
| P05 | code_lookup | wrong_source |
| P06 | code_lookup | unchecked_answer, wrong_source |
| P13 | code_lookup | refusal_then_answer, false_refusal |
| P19 | symptom | false_refusal |
| P20 | symptom | refusal_then_answer |
| P25 | symptom | unchecked_answer, wrong_source |
| P41 | multi_part | refusal_then_answer |
| P43 | multi_part | unchecked_answer, wrong_source |
| P56 | cross_article | refusal_then_answer |
