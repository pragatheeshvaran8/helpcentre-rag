# Week 6: before and after, per problem type

- before: `before`   after: `after`
- Prompt changed between runs: **True**

## Headline

| | passed | rate |
|---|---|---|
| before | 33/60 | 55.0% |
| after | 40/60 | 66.7% |
| change | **+7** | +11.7 pts |

## By problem type

| Kind | before | after | change |
|---|---|---|---|
| code_lookup | 11/18 | 12/18 | +1 |
| cross_article | 0/3 | 2/3 | +2 |
| multi_part | 5/6 | 5/6 | +0 |
| noisy | 3/5 | 2/5 | -1 |
| out_of_corpus | 3/3 | 3/3 | +0 |
| policy | 2/7 | 2/7 | +0 |
| procedure | 3/6 | 5/6 | +2 |
| symptom | 2/8 | 5/8 | +3 |
| vague | 4/4 | 4/4 | +0 |

## By failure mode

| Mode | before | after | change |
|---|---|---|---|
| retrieval_miss | 0 | 0 | +0  |
| false_refusal | 21 | 17 | -4 **better** |
| unchecked_answer | 4 | 1 | -3 **better** |
| fabricated_citation | 0 | 0 | +0  |
| wrong_source | 5 | 3 | -2 **better** |
| refusal_then_answer | 10 | 5 | -5 **better** |
| missed_refusal | 0 | 0 | +0  |

## Week 5 regressions

| | before | after |
|---|---|---|
| held | 2/6 | 2/6 |
| recurred | P31, P34 | P02, P17, P31, P34 |
