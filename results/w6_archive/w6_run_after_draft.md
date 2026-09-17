# Week 6 eval run: `after`

- Cases scored: 60 of 60
- Passed every applicable assertion: **40/60** (66.7%)
- Mean assertion score: 0.8656

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
| prompt_sha | `6f7f9b1487018664` |

## Pass rate by problem type

| Kind | Passed | Rate |
|---|---|---|
| code_lookup | 12/18 | 67% |
| cross_article | 2/3 | 67% |
| multi_part | 5/6 | 83% |
| noisy | 2/5 | 40% |
| out_of_corpus | 3/3 | 100% |
| policy | 2/7 | 29% |
| procedure | 5/6 | 83% |
| symptom | 5/8 | 62% |
| vague | 4/4 | 100% |

## Failure modes

| Mode | Count |
|---|---|
| retrieval_miss | 0 |
| false_refusal | 17 |
| unchecked_answer | 1 |
| fabricated_citation | 0 |
| wrong_source | 3 |
| refusal_then_answer | 5 |
| missed_refusal | 0 |

## Regressions from Week 5

- Pinned: 6
- Held: 2
- Recurred: P02, P17, P31, P34
- Broke a new way: none

## Failing cases

| Case | Kind | Failure modes |
|---|---|---|
| P02 | code_lookup | false_refusal |
| P05 | code_lookup | false_refusal |
| P11 | code_lookup | false_refusal |
| P12 | code_lookup | refusal_then_answer, false_refusal |
| P13 | code_lookup | refusal_then_answer, false_refusal |
| P17 | code_lookup | refusal_then_answer, false_refusal |
| P19 | symptom | false_refusal |
| P20 | symptom | refusal_then_answer, false_refusal |
| P26 | symptom | unchecked_answer, wrong_source |
| P27 | policy | false_refusal |
| P28 | policy | refusal_then_answer, false_refusal |
| P29 | policy | false_refusal |
| P31 | policy | false_refusal |
| P33 | policy | wrong_source |
| P34 | procedure | false_refusal |
| P41 | multi_part | false_refusal |
| P46 | noisy | wrong_source |
| P47 | noisy | false_refusal |
| P49 | noisy | false_refusal |
| P55 | cross_article | false_refusal |
