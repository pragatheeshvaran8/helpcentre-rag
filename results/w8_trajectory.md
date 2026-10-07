# Week 8: the outcome-vs-trajectory gap

Scored over the twelve Week 7 agent runs. Nothing here calls a model.

## The gap

| | count |
|---|---|
| Tickets | 12 |
| **Outcome** passed | **12/12** |
| **Trajectory** clean | **10/12** |
| **Right answer, wrong path** | **2** |

The gap is on T11, T12.

Outcome-only scoring gives a perfect card. It is wrong about two of
the twelve, and it is wrong in the direction that matters: those two
look fine and will not stay fine.

## Cost per task

| | calls |
|---|---|
| mean | 3.42 |
| median | 3.0 |
| p99 | 7 |
| total | 41 |

p99 on twelve runs is the worst run. Saying so is more useful than a
percentile that implies more data than exists.

## Tool choice

Tool-choice accuracy is **100%**. The agent picks the
right tool every time. Picking the tool is not the problem. Knowing
when to stop is.

Perfect route, no wasted steps: **10/12**. 
Extra steps beyond the ideal path: **8**.

## Failure modes on the path

| Mode | count |
|---|---|
| `looped` | 2 |
| `never_finished` | 2 |
| `wasted_step` | 2 |
| `quiet_give_up` | 1 |
| `unparsed_step` | 1 |

## Per ticket

| Ticket | shape | outcome | path | tool choice | extra steps | modes |
|---|---|---|---|---|---|---|
| T01 | multi | pass | clean | 100% | 0 | - |
| T02 | multi | pass | clean | 100% | 0 | - |
| T03 | multi | pass | clean | 100% | 0 | - |
| T04 | multi | pass | clean | 100% | 0 | - |
| T05 | multi | pass | clean | 100% | 0 | - |
| T06 | multi | pass | clean | 100% | 0 | - |
| T07 | single | pass | clean | 100% | 0 | - |
| T08 | single | pass | clean | 100% | 0 | - |
| T09 | single | pass | clean | 100% | 0 | - |
| T10 | single | pass | clean | 100% | 0 | - |
| T11 | refuse | pass | **broken** | 100% | 4 | looped, wasted_step, unparsed_step, quiet_give_up, never_finished |
| T12 | refuse | pass | **broken** | 100% | 4 | looped, wasted_step, never_finished |

## The loops, step by step

- **T11**: step 1 = step 2, step 1 = step 3, step 1 = step 6, step 2 = step 3, step 2 = step 5, step 2 = step 6, step 3 = step 6, step 5 = step 6
- **T12**: step 2 = step 6, step 3 = step 4, step 3 = step 5, step 4 = step 5

