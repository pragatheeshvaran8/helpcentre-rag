# Week 6: before and after, per problem type

- before: `before`   after: `after`
- Prompt changed between runs: **True**
- before `prompt_sha` `9a61e3569211b597`, after `4a4b6fc6a1a4e1af`
- Every other key in `COMPARABLE_KEYS` is identical. The prompt is the only
  thing that moved.

> **MATCHED SUBSET, 43 of 60 cases.** The `after` run did not finish: 17 cases
> never generated. Every number below is computed over the 43 cases that BOTH
> runs scored, so the two columns describe the same questions.
>
> This is not the full eval set. The headline for the whole 60 is not known
> until `after` finishes.
>
> Not run in `after`: P07, P14, P24, P33, P34, P36, P40, P42, P44, P46, P48,
> P49, P50, P52, P53, P54, P58
>
> Written by hand from `before.json` and `after.json`. Re-running
> `python -m evals.run_evals --compare before after` will overwrite this file
> with the generated version, which borrows one denominator for both rows and
> so prints `34/60` where it means `34/43`.

## Headline

| | passed | rate |
|---|---|---|
| before | 20/43 | 46.5% |
| after | 34/43 | 79.1% |
| change | **+14** | +32.6 pts |

## By problem type

| Kind | before | after | change |
|---|---|---|---|
| code_lookup | 9/16 | 13/16 | +4 |
| cross_article | 0/3 | 2/3 | +2 |
| multi_part | 2/3 | 1/3 | -1 |
| noisy | 0/1 | 1/1 | +1 |
| out_of_corpus | 2/2 | 2/2 | +0 |
| policy | 2/6 | 6/6 | +4 |
| procedure | 2/4 | 4/4 | +2 |
| symptom | 2/7 | 4/7 | +2 |
| vague | 1/1 | 1/1 | +0 |

## By failure mode

| Mode | before | after | change |
|---|---|---|---|
| retrieval_miss | 0 | 0 | +0  |
| false_refusal | 18 | 2 | -16 **better** |
| unchecked_answer | 4 | 3 | -1 **better** |
| fabricated_citation | 0 | 0 | +0  |
| wrong_source | 4 | 4 | +0  |
| refusal_then_answer | 10 | 4 | -6 **better** |
| missed_refusal | 0 | 0 | +0  |

`retrieval_miss` is 0 in both runs. The answering chunk was in the context
every time, in both. Nothing about retrieval changed, and nothing about
retrieval explains the gain.

`missed_refusal` is 0 in both runs. The prompt was loosened about when to
refuse, and the app still refused every question it should have. Four of the
seven guard cases have not run yet, so this holds on 3 of 7.

## Week 5 regressions

| | before | after |
|---|---|---|
| held | 1/4 | 4/4 |
| recurred | P31 | none |
| new_break | P02, P23 | none |

Two of the six pinned regressions, P17 and P34, are among the 17 cases that did
not run, so this covers 4 of 6.
