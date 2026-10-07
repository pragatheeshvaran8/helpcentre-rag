# Week 8: closing the top failure mode

**The mode:** `looped`. The agent asks the same question again in
different words, and the Week 7 guard does not see it because it only
compares one action to the one immediately before it, exactly.

**The fix:** an action now counts as repeated when it asks the same
question as any earlier action, measured by word overlap.

**One variable moved.** Same prompts, same tools, same tickets, same
model. Only `Budget.similar_guard` changes.

Compared over the 11 tickets both runs scored.

## The number

| | before | after |
|---|---|---|
| Outcome passed | 11/11 | 11/11 |
| **Trajectory clean** | **9/11** | **9/11** |
| **Right answer, wrong path** | **2** | **2** |
| **Tickets that looped** | **1** | **0** |
| Calls, mean | 3.18 | 3.0 |
| Calls, median | 3 | 3 |
| Calls, p99 (worst run) | 9 | 5 |
| Calls, total | 35 | 33 |

## Per ticket

| Ticket | before calls | after calls | before modes | after modes |
|---|---|---|---|---|
| T01 | 3 | 3 | - | - |
| T02 | 3 | 3 | - | - |
| T03 | 3 | 3 | - | - |
| T04 | 3 | 3 | - | - |
| T05 | 4 | 4 | - | - |
| T07 | 2 | 2 | - | - |
| T08 | 2 | 2 | - | - |
| T09 | 2 | 2 | - | - |
| T10 | 2 | 2 | - | - |
| T11 | 2 | 4 | wasted_step, never_finished | wasted_step, unparsed_step, never_finished |
| T12 | 9 | 5 | looped, wasted_step, unparsed_step, never_finished | wasted_step, unparsed_step, quiet_give_up, never_finished |

## The guard against a cheap win

Stopping earlier is trivially cheaper and would be worthless if the
answers got worse. Outcome pass rate is reported above for exactly
that reason. A fix that cuts calls and drops answers is not a fix.

