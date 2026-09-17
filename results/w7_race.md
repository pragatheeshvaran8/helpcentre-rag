# Week 7: agent against fixed workflow

- Tickets: 12  (6 multi-part, 4 single, 2 not in corpus)
- Model: `poolside/laguna-s-2.1:free`
- Grounding prompt: `4a4b6fc6a1a4e1af`   agent loop prompt: `v3`

## Speed, cost, reliability

| | agent | fixed workflow |
|---|---|---|
| Tickets scored | 12 | 12 |
| **Speed** median s/ticket | 28.95 | 3.52 |
| Slowest ticket | 89.33s | 19.86s |
| **Cost** LLM calls total | 41 | 12 |
| Calls per ticket | 3.42 | 1.0 |
| **Reliability** passed | 12/12 | 8/12 |
| Ran to completion | 10/12 | 12/12 |
| Errors | 0 | 0 |

## Did it answer the whole ticket?

A two-part ticket with one part answered is not half right. It is wrong.

| | agent | fixed workflow |
|---|---|---|
| Parts cited, all tickets | 100% | 71% |
| Parts cited, multi-part only | 100% | 62% |
| Multi-part tickets fully answered | 6/6 | 3/6 |

## By ticket shape

| Shape | agent passed | workflow passed | agent calls | workflow calls |
|---|---|---|---|---|
| multi | 6/6 | 3/6 | 19 | 6 |
| single | 4/4 | 4/4 | 8 | 4 |
| refuse | 2/2 | 1/2 | 14 | 2 |

## Why the agent stopped

| Reason | agent | workflow |
|---|---|---|
| finished | 10 | 12 |
| step_limit | 2 | 0 |

## Per ticket

| Ticket | shape | runner | pass | parts cited | steps | calls | s |
|---|---|---|---|---|---|---|---|
| T01 | multi | agent | yes | 2/2 | 3 | 3 | 37.15 |
| T01 | multi | workflow | no | 0/2 | 2 | 1 | 19.86 |
| T02 | multi | agent | yes | 2/2 | 3 | 3 | 29.37 |
| T02 | multi | workflow | yes | 2/2 | 2 | 1 | 8.97 |
| T03 | multi | agent | yes | 2/2 | 3 | 3 | 35.15 |
| T03 | multi | workflow | yes | 2/2 | 2 | 1 | 4.46 |
| T04 | multi | agent | yes | 2/2 | 3 | 3 | 11.32 |
| T04 | multi | workflow | no | 0/2 | 2 | 1 | 3.07 |
| T05 | multi | agent | yes | 3/3 | 4 | 4 | 28.52 |
| T05 | multi | workflow | no | 2/3 | 2 | 1 | 7.84 |
| T06 | multi | agent | yes | 2/2 | 3 | 3 | 55.48 |
| T06 | multi | workflow | yes | 2/2 | 2 | 1 | 4.92 |
| T07 | single | agent | yes | 1/1 | 2 | 2 | 9.89 |
| T07 | single | workflow | yes | 1/1 | 2 | 1 | 2.85 |
| T08 | single | agent | yes | 1/1 | 2 | 2 | 12.89 |
| T08 | single | workflow | yes | 1/1 | 2 | 1 | 3.97 |
| T09 | single | agent | yes | 1/1 | 2 | 2 | 9.42 |
| T09 | single | workflow | yes | 1/1 | 2 | 1 | 1.56 |
| T10 | single | agent | yes | 1/1 | 2 | 2 | 9.36 |
| T10 | single | workflow | yes | 1/1 | 2 | 1 | 3.02 |
| T11 | refuse | agent | yes | 0/0 | 6 | 7 | 70.42 |
| T11 | refuse | workflow | yes | 0/0 | 2 | 1 | 2.12 |
| T12 | refuse | agent | yes | 0/0 | 6 | 7 | 89.33 |
| T12 | refuse | workflow | no | 0/0 | 2 | 1 | 2.95 |

## Which one would I ship

**agent.**

The agent fully answers 6 of 6 multi-part tickets against 3 for the fixed workflow. It costs 3.42 calls a ticket against 1.0, and is 8.2x slower. Half an answer on a support ticket is a failure, so the coverage gap is worth the cost.

| Ticket shape | better runner |
|---|---|
| multi | agent |
| single | workflow |
| refuse | agent |

The rule that picked this is written in `evals/w7_race.py` and was
written before the race ran. Coverage of multi-part tickets decides
it, cost breaks ties, and a gap smaller than one whole ticket counts
as no gap on a set this size.
