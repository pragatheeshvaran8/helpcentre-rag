# Week 6 eval run: `before`

- Cases scored: 60 of 60
- Passed every applicable assertion: **33/60** (55.0%)
- Mean assertion score: 0.8033

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
| prompt_sha | `9a61e3569211b597` |

## Pass rate by problem type

| Kind | Passed | Rate |
|---|---|---|
| code_lookup | 11/18 | 61% |
| cross_article | 0/3 | 0% |
| multi_part | 5/6 | 83% |
| noisy | 3/5 | 60% |
| out_of_corpus | 3/3 | 100% |
| policy | 2/7 | 29% |
| procedure | 3/6 | 50% |
| symptom | 2/8 | 25% |
| vague | 4/4 | 100% |

## Failure modes

| Mode | Count |
|---|---|
| retrieval_miss | 0 |
| false_refusal | 21 |
| unchecked_answer | 4 |
| fabricated_citation | 0 |
| wrong_source | 5 |
| refusal_then_answer | 10 |
| missed_refusal | 0 |

## Regressions from Week 5

- Pinned: 6
- Held: 2
- Recurred: P31, P34
- Broke a new way: P02, P23

## Judge

> These numbers mean nothing until `w6_validate_judge.py` shows the
> judge agreeing with hand grading.

- Judged: 32, not judged: 0
- Faithful: 27/32 (84%)
- Relevant: 31/32 (97%)
- Unfaithful: P02, P06, P22, P35, P46
- Irrelevant: P46

## Failing cases

| Case | Kind | Failure modes |
|---|---|---|
| P01 | code_lookup | refusal_then_answer, false_refusal |
| P02 | code_lookup | unchecked_answer, wrong_source |
| P03 | code_lookup | refusal_then_answer, false_refusal |
| P05 | code_lookup | false_refusal |
| P06 | code_lookup | unchecked_answer, wrong_source |
| P12 | code_lookup | false_refusal |
| P13 | code_lookup | refusal_then_answer, false_refusal |
| P19 | symptom | false_refusal |
| P20 | symptom | false_refusal |
| P21 | symptom | false_refusal |
| P22 | symptom | refusal_then_answer, unchecked_answer, wrong_source |
| P23 | symptom | refusal_then_answer, false_refusal |
| P24 | symptom | false_refusal |
| P27 | policy | false_refusal |
| P28 | policy | false_refusal |
| P29 | policy | refusal_then_answer, false_refusal |
| P31 | policy | false_refusal |
| P33 | policy | false_refusal |
| P34 | procedure | false_refusal |
| P35 | procedure | unchecked_answer, wrong_source |
| P38 | procedure | refusal_then_answer, false_refusal |
| P41 | multi_part | refusal_then_answer, false_refusal |
| P46 | noisy | wrong_source |
| P47 | noisy | refusal_then_answer, false_refusal |
| P55 | cross_article | false_refusal |
| P56 | cross_article | false_refusal |
| P57 | cross_article | refusal_then_answer |
