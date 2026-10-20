# Week 11: the app watching itself

Four things, in the order the mentor asks about them.

## 1. The log

| | |
|---|---|
| Traces | 82 |
| Days covered | 15 (2026-09-28 to 2026-10-12) |
| LLM calls recorded | 252 |
| Refusals | 10 |
| Median latency | 16640 ms |
| p95 latency | 62150 ms |

Every request carries a trace id, a timestamp, the question, the answer,
the chunk ids it was built from, what it cited, and **a span per step**.

A span is a step with its own milliseconds, tokens and cost. One total
would hide where the time and money went, which is the whole reason
Week 10 could say the squad's manager spent 5,174 input tokens and
produced no answer.

## 2. The support drill

**The complaint, as forwarded:**

> Finance flagged something from about a week ago. Someone asked us about a refund where the card had been lost in the migration, and we apparently told them it would go back on the original card. Finance says that is wrong and it should have been account credit. No ticket number, sorry.

No trace id. No exact wording. A rough date and the word 'refund'.

**How it narrowed:**

| Filter | Traces left |
|---|---|
| all traces | 34 |
| matched any of 4 complaint word(s) | 12 |

**Found `a66f0fd87c39`** over 34 traces:

| Step | Time |
|---|---|
| Search | **8.2ms** |
| Proof, reading the cited chunk | 0.5ms |
| One-off index load, before the clock | 18932.4ms |

**Why it is wrong:**

> HC-4003-structured-006 says: "the refund cannot be returned to the card and must be issued as account credit instead". The answer says the money goes back to the original card, and never mentions account credit.

That last step is what makes it a drill rather than a lucky grep. The
answer cited a real chunk, and said the opposite of what the chunk says.
Every deterministic check in this project passes it, because they all
ask whether the citation resolves, not whether it agrees.

## 3. Cost per request, measured and improved

| | before | after |
|---|---|---|
| Cost per request | $0.00025401 | **$0.00006030** |
| Tokens per request | 1316.3 | **320.4** |
| LLM calls over the log | 254 | **48** |

**Cost saving: 76.3%.** Cache hit rate 81.9%: 68 exact, 0 similar.

**The improvement is an answer cache**, fenced by model, prompt
fingerprint and corpus fingerprint. Change any of those and the cache
empties rather than serving stale answers under new settings.

### The risk, which decides whether the saving counts

A cache that serves the wrong answer is not a saving. It is a bug with
a good dashboard. So the wrong answers are counted too.

| Similarity threshold | Hit rate | Saving | Wrong answers served |
|---|---|---|---|
| 0.5 | 81.9% | 76.3% | 0/48 |
| 0.7 | 81.9% | 76.3% | 0/48 |
| 0.8 | 81.9% | 76.3% | 0/48 |
| 0.9 | 81.9% | 76.3% | 0/45 |

**Zero wrong answers at every threshold**, and the reason is not the
threshold. It is the code fence: two questions that differ only by
their error code are never treated as the same question.

`ERR-4032` against `ERR-4044` in the same sentence scores **0.818**
word overlap, which is above the 0.8 threshold. Without the fence that
near-miss is served, and a customer gets the fix for the wrong problem.

## 4. The failure, now a test

| Check | Result |
|---|---|
| R01 catches the answer that failed | yes |
| R01 allows a correct answer | yes |

Both directions matter. A check that catches the bug but also fires on
correct answers is not a guard, it is an alarm nobody will keep.

The case records the trace id it came from, so six months from now the
log can answer why it exists. A regression with no provenance gets
deleted by the next person tidying up.

### Asked again, live

- Trace: `cf68ad678877`
- Result: **passes**

```
If the card token was dropped during migration, the refund cannot be returned to the original card and must be issued as account credit instead. [HC-4003-structured-006]
```

## The 10x plan: what breaks first

At ten times this traffic, in the order it breaks:

1. **The provider's rate limit, long before anything of ours.** This
   project hit the free tier's daily cap in six of the last eight weeks.
   Ten times the traffic means that at 2am instead of 4pm. The fix is a
   paid tier and a queue, not code.
2. **The trace log.** One JSONL file per day, read whole into memory by
   every search. At 82 traces that is 2ms. At 50,000 a day it is a
   problem, and the fix is the one every team reaches for: ship the
   traces to something built for them. The shape here is already the
   trace-and-span shape LangSmith, Phoenix and OpenTelemetry take, so
   the change is `obs/store.py` and nothing else.
3. **The answer cache's memory.** It is a list scanned linearly on every
   lookup. Fine at hundreds of entries, not at hundreds of thousands.
4. **The MCP servers.** One subprocess per server per agent process. Ten
   times the concurrency means ten times the processes, each loading its
   own copy of the embedding model.

**What does NOT break:** retrieval. It is a local index over 34 chunks
and has never been the bottleneck in nine weeks of measurement.

## What this does NOT do

- **The log is backfilled.** The questions, answers, chunk ids and token
  counts are real and come from the Weeks 7 to 10 caches. **The
  timestamps are invented**, because the caches record no wall-clock date
  and the drill needs to narrow by day. Every backfilled trace is marked
  `backfilled: true`.
- **The hit rate is flattered.** The log replays eval runs, which asked
  the same twelve questions many times. Real support traffic is more
  varied, so 81.7% is an upper bound, not a forecast.
- **The similarity layer contributed nothing here.** Every hit was exact.
  The risky half of the cache is the half this traffic never exercised.
- **The planted answer is planted.** It is marked in the log, and a test
  asserts the search never filters on that marker. The drill is honest
  about the haystack while being honest that the needle was placed.
- **No rotation, no retention, no PII redaction.** All three are real
  production concerns and none is built.
- **`contradicts_its_citation` checks one rule**, not faithfulness in
  general. A general judge is what Week 6 built and then refused to
  trust.

## Reproducing it

```bash
python -m evals.run_w11 --all     # all four parts. Free.
python -m evals.run_w11 --drill   # just the drill. Free.
python -m evals.run_w11 --live    # ask the pinned question again. ~3 calls.
python test_acceptance.py
```

