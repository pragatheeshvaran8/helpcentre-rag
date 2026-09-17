# Week 7 — Agent Loops: when the loop earns its cost, and when it does not

The task was to build an agent by hand, build the same thing as a plain fixed
sequence, and compare them on speed, cost and reliability. Both exist, both ran
on the same twelve tickets, and both were scored by the same rules.

The short version: the agent wins, but only on one ticket shape, and it is
8.2 times slower and 3.4 times dearer everywhere else.

---

## 0. What this week produced

| | |
|---|---|
| A hand-built agent | `agent/`, five files, no framework |
| A fixed workflow to race it | `agent/workflow.py`, the Week 3 to 6 app |
| Twelve tickets, three shapes | `evals/w7_tickets.py` |
| One command | `python -m evals.run_race` |
| Every step, in full | `results/w7_agent_steps.md` |
| The race | `results/w7_race.md` |
| 52 new acceptance checks | `test_acceptance.py`, now 121 |

The loop is ordinary Python. No LangChain, no LangGraph, no provider function
calling. The whole decision cycle is one `while` block in `agent/loop.py`, and
it fits on a screen.

---

## 1. The number

Twelve tickets, both runners, complete.

| | agent | fixed workflow |
|---|---|---|
| **Speed**, median seconds per ticket | 28.95 | **3.52** |
| Slowest ticket | 89.33s | 19.86s |
| **Cost**, LLM calls total | 41 | **12** |
| Calls per ticket | 3.42 | **1.0** |
| **Reliability**, tickets passed | **12/12** | 8/12 |
| Ran to completion | 10/12 | **12/12** |
| Errors | 0 | 0 |

The agent is 8.2x slower and costs 3.4x more calls. It also passes every
ticket, and the fixed workflow does not.

---

## 2. The metric that actually decides it

Pass or fail is too coarse for a ticket that asks three things.

The Week 6 assertion checks were built for one-question cases, so
`context_holds_answer` returns true as soon as **any** requirement is met. A
two-part ticket with one part answered passes them. That was verified directly,
not assumed:

```
both parts answered   passed=True   coverage cited 2/2
one part answered     passed=True   coverage cited 1/2
```

So Week 7 adds **part coverage**, computed per requirement in
`evals/w7_race.py`. A ticket is only fully answered when every part of it is
cited from an article that really holds that part.

| | agent | fixed workflow |
|---|---|---|
| Parts cited, all tickets | **100%** | 71% |
| Parts cited, multi-part only | **100%** | 62% |
| Multi-part tickets fully answered | **6/6** | **3/6** |

A support agent handed half an answer has to go and look up the other half
themselves. That is not a partial success, it is a failure with a friendly
tone.

---

## 3. Where the fixed workflow breaks, and why it has to

The fixed workflow retrieves once, on the whole ticket, then answers. There is
no second look. When a ticket asks two unrelated things, both go into one query
and a fixed top-k has to cover two topics at once.

Three multi-part tickets failed, all for that reason.

| Ticket | Workflow | Agent | What the ticket asked |
|---|---|---|---|
| T01 | **0 of 2 parts** | 2 of 2 | ERR-4032 on an invoice, and ERR-7215 on VAT |
| T04 | **0 of 2 parts** | 2 of 2 | A MIG-220 badge, and the v1 API sunset policy |
| T05 | 2 of 3 parts | 3 of 3 | ERR-7208, ERR-5199, and voiding a paid invoice |

T01 is the clearest. The workflow **refused it outright**, carrying
`false_refusal`, despite both answers being in the corpus. One blended query
across an invoicing article and a tax article retrieved a top-k that served
neither well enough for the model to commit.

The agent worked the same ticket in three steps:

```
step 1: lookup_error_code(code='ERR-4032')
step 2: lookup_error_code(code='ERR-7215')
step 3: finish(...)
        finished  3 steps  3 calls  37.1s
```

Two lookups, two citations, both parts covered. Nothing clever happened. It
simply got to ask twice.

---

## 4. Where the agent is pure waste

This is the half of the week that matters more.

On single-part tickets the two runners are **identical on outcome**:

| | agent | fixed workflow |
|---|---|---|
| Passed | 4/4 | 4/4 |
| Parts cited | 4/4 | 4/4 |
| LLM calls | 8 | **4** |
| T09 elapsed | 9.42s | **1.56s** |

Double the cost, six times the wait, same answer. Every extra step is the model
re-deciding something that was never in doubt.

**If the ticket asks one thing, the loop is overhead with a nicer story.**

---

## 5. The worst case, stated plainly

The two out-of-corpus tickets cost the agent 14 of its 41 calls.

| Ticket | Steps | Calls | Seconds | Stop reason |
|---|---|---|---|---|
| T11 | 6 | 7 | 70.4 | `step_limit` |
| T12 | 6 | 7 | 89.3 | `step_limit` |

Both got the right answer. Neither got there by deciding to. The agent searched,
found nothing, searched again, and kept going until the **budget** stopped it
and forced it to answer from what it had.

The fixed workflow refused both in one call and about two seconds.

**A third of the agent's total cost went on the two tickets where there was
nothing to find.** An agent has no natural way to conclude that something is
absent. It can always try one more query. That is not a tuning problem, it is
the shape of the thing.

It also failed one of them in a way worth naming: the workflow answered T12
when it should have refused. The agent refused correctly. So the loop is not
uniformly worse here, it is uniformly more expensive.

---

## 6. Stop conditions, and why they are load-bearing

A loop with a model deciding when to exit has no natural end. Four independent
limits are enforced in `agent/budget.py`, and the loop cannot run without them.

| Limit | Default | What it catches |
|---|---|---|
| Steps | 6 | The blunt backstop |
| LLM calls | 8 | Cost, counting retries |
| Wall clock | 120s | A hanging provider |
| Repeated action | warn once, then stop | A model going in circles |

All four are proven by tests that drive the loop with a scripted model, so they
cost nothing to verify and do not depend on the API being up.

Two of twelve tickets ended on `step_limit`, and both still produced a correct
cited answer. **Hitting a limit is an ordinary outcome, not a crash.** The run
records `stop_reason`, answers from what it gathered, and is never reported as
having completed.

The repeat rule was changed after watching a real run. The first version stopped
the loop dead on any repeat, and it fired at the exact moment the agent had both
facts and should have called `finish`. It now warns once:

> "You just ran that exact call. Either look up something you have NOT looked
> up yet, or, if you already have the facts, call finish now."

A second repeat still stops it.

---

## 7. What the live runs taught that the design did not

Five real bugs were found by running single tickets before spending quota on
the full race. All five came from watching output, none from reading code.

**The exact lookup was truncating the answer away.** `lookup_error_code`
returned 2,730 characters: three chunks, each clipped at 900. The chunk holding
ERR-7215 is 999 characters, and the 99 that were cut were the fix. The model
could see the code and not its answer, said so in its own thought line, and
spent three further steps hunting for something it had already been handed:

> "the ERR-7215 row is truncated. I need the full cause and fix text for
> ERR-7215."

An exact lookup now returns the table header plus the one row naming that code.
**319 characters instead of 2,730**, and it cannot be clipped. That one fix took
T01 from 6 steps and 7 calls to 3 and 3.

**The out-of-budget answer had no citations at all.** The first version used a
short hand-written wrap-up prompt. The model produced a factually correct
answer for both parts of T01 and cited nothing, so it scored zero. A three-line
instruction does not hold against a prompt that took Week 6 to tune. The
fallback now goes through the real grounding prompt, which also keeps the race
fair: both runners answer under identical rules.

**A 429 was being cached as a result.** That ticket would have been frozen as
permanently failed. Provider errors are no longer cached. Budget exhaustion
still is, because that is the agent genuinely running out.

**Two different 429s were treated the same.** `free-models-per-day` is fatal
until the reset. `temporarily rate-limited upstream` clears in seconds, and the
provider's own message says "Please retry shortly". Probing the model three
times gave two upstream failures and then a success. The code was throwing away
whole tickets on a recoverable error. It now retries only the transient one,
with backoff, at all three call sites so neither runner gets more chances than
the other.

**A raw newline inside JSON is invalid JSON**, and a refusal is two lines by
design, so the model emits one every time it refuses. That would have cost a
step on every refusal ticket.

---

## 8. Which one to ship

**The agent, on this ticket mix.** The rule that picked it is in
`evals/w7_race.py`, it was written before the race ran, and it is applied
mechanically:

1. Materially better coverage of multi-part tickets wins those tickets.
2. On single-part tickets, cost breaks the tie.
3. A gap smaller than one whole ticket counts as no gap on a set this size.

| Ticket shape | Better runner |
|---|---|
| multi | agent |
| single | **workflow** |
| refuse | agent |

The honest recommendation is not "the agent". It is **route by shape**. A
cheap classifier on the way in, sending one-problem tickets to the fixed
sequence and several-problem tickets to the loop, gets the coverage without
paying 3.42 calls for a ticket that needs one. That is not built here, because
this week is a comparison and adding a router would make it a three-way one.

---

## 9. What this week does NOT tell you

- **Twelve tickets is small.** A one-ticket swing moves a rate by 8 points.
  The multi-part gap is 3 tickets wide, which is why it is reported as a
  finding and the single-part tie is not.
- **The ticket mix was chosen.** Half the set is multi-part, which is more than
  a real support queue. The agent's overall advantage is therefore flattered by
  construction. The per-shape table is the honest view, not the headline.
- **One model, one free tier.** `poolside/laguna-s-2.1:free` is a weak
  instruction-follower. It leaked `<tool_call>` tags and returned an empty
  reply. A stronger model would change the step counts and might close the
  coverage gap from the workflow side.
- **Speed is wall clock on a shared free pool**, so it measures queueing as
  much as work. Calls is the more honest cost number, and it is the one the
  ship rule uses.
- **No judge ran.** Coverage and the assertion checks carry the whole result.

---

## 10. Reproducing it

```bash
python -m evals.run_race                  # both runners, every ticket
python -m evals.run_race --runner agent   # one side
python -m evals.run_race --ticket T01 -v  # watch one ticket, step by step
python -m evals.run_race --report         # rescore the cache, no API calls
python test_acceptance.py                 # 121 checks
```

Every finished ticket is cached, keyed by runner, ticket and a fingerprint of
the prompts and loop version that produced it. A run interrupted by the daily
cap resumes and pays only for what is missing. A record produced by an older
loop stops matching and is reported as missing rather than scored beside
current ones.

---

## 11. Files

| File | What it is |
|---|---|
| `agent/tools.py` | Three tools, and descriptions that distinguish themselves |
| `agent/loop.py` | The loop, plus the ReAct protocol and the parser |
| `agent/budget.py` | The four stop conditions |
| `agent/memory.py` | Scratchpad, plus every chunk seen |
| `agent/workflow.py` | The fixed sequence, wrapping the Week 3 to 6 app |
| `evals/w7_tickets.py` | Twelve tickets, three shapes |
| `evals/w7_race.py` | Scoring, part coverage, and the ship rule |
| `evals/run_race.py` | The one command |
| `results/w7_race.md` | The race |
| `results/w7_agent_steps.md` | Every step of every agent run |
| `results/w7_race/` | Cached runs and scores |

---

## 12. The one-line answer to the week's question

An agent earns its cost when the next thing to look up depends on what the last
lookup returned. On this corpus that is true for tickets carrying several
unrelated problems, and false for everything else, and "everything else" is
most of a support queue.
