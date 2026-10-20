# Week 11 — Production: the app watching itself

The task was four things: add logging that can find any past answer, run a
support drill against a planted bad answer from a vague complaint, measure cost
per request and improve it, and turn one real failure into a permanent test.

All four are done. The headline numbers: the drill found the bad answer in
**5.4 milliseconds** over 35 traces, and cost per request fell **76%** with
**zero wrong answers served**.

---

## 0. What this week produced

| | |
|---|---|
| Per-request tracing with spans | `obs/trace.py` |
| The log, and how it is read back | `obs/store.py` |
| The support drill's search | `obs/search.py` |
| Real traffic, replayed into the log | `obs/backfill.py` |
| The planted bad answer, and its proof | `obs/plant.py` |
| The cost improvement | `obs/cache.py` |
| The saving AND the risk | `obs/measure.py` |
| The failure, pinned | `evals/w11_regressions.py` |
| One command | `evals/run_w11.py` |
| 72 new acceptance checks | `test_acceptance.py`, now 315 |

---

## 1. The log, and time and cost per step

**83 traces over 16 days.** Every request carries a trace id, a timestamp, the
question, the answer, the chunk ids it was built from, what it cited, the
config it ran under, and **a span per step**.

**A span is a step with its own milliseconds, tokens and cost.** Here is the
live request this week made, exactly as logged:

| Step | ms | in | out | cost |
|---|---|---|---|---|
| `toolbox:connect` | 18,028 | 0 | 0 | $0 |
| `agent:step 1` | 5,908 | 936 | 58 | $0.00017520 |
| `tool:search_help_centre` | 17,569 | 0 | 0 | $0 |
| `agent:step 2` | 9,433 | 1,572 | 102 | $0.00029700 |
| `tool:finish` | 0 | 0 | 0 | $0 |
| **TOTAL** | **54,299** | **2,508** | **160** | **$0.00047220** |

**One total would have said "54 seconds" and stopped there.** The spans say
something you can act on: **36 of those 54 seconds are MCP start-up and the
first search**, not the model. The two model calls took 15 seconds between
them.

If you were asked to make this faster, the lump number sends you to the model.
The spans send you to the warm-up, which is where the time actually is.

### Why the log is shaped like this

`obs/store.py` writes newline-delimited JSON, one file per UTC day. A crash
mid-write loses one line rather than the file, and `grep` works on it.

A real deployment ships these to LangSmith, Phoenix or an OpenTelemetry
collector. **The shape here is the shape those take**: a trace with spans under
it. Swapping the sink is a change to one file.

---

## 2. The support drill

**The complaint, as forwarded:**

> Finance flagged something from about a week ago. Someone asked us about a
> refund where the card had been lost in the migration, and we apparently told
> them it would go back on the original card. Finance says that is wrong and it
> should have been account credit. No ticket number, sorry.

**No trace id. No exact wording. A rough date and the word "refund".**

### How it narrowed

| Filter | Traces left |
|---|---|
| All traces in the date window | 35 |
| Matched any of 4 rare words from the complaint | 14 |
| Ranked by how rare those words are | **top hit, score 8.16** |

The second-place hit scored 4.16. **The gap is not luck**: "migration" and
"token" are rare in this log, and the ranking weights a word by how rare it is.
A match on "card" counts for almost nothing because half the corpus is about
cards.

### How long it took

| Step | Time |
|---|---|
| **Search over 35 traces** | **5.4 ms** |
| Proof, reading the cited chunk | 0.3 ms |
| One-off index load, before the clock | 13,828 ms |

**The index load is honest and separate.** It is a start-up cost paid once, not
search time. An earlier version timed it inside the drill and reported 15.6
seconds for a 5ms search, which answers "quickly?" with the wrong number.

### Why it is wrong

> `HC-4003-structured-006` says: *"the refund cannot be returned to the card and
> must be issued as account credit instead"*. The answer says the money goes
> back to the original card, and never mentions account credit.

**This step is what makes it a drill rather than a lucky grep.** A support
engineer cannot hand a trace id to an angry customer on a hunch. They need the
line from the article beside the line from the answer.

**The live run made that concrete.** Asking the pinned question again put a
second trace in the log with the identical question and the correct answer.
Searched without a date filter, the two tie at a score of 9.06: same words,
same rarity, same rank.

**Search cannot tell them apart. The proof step can.** One contradicts the
chunk it cites and one agrees with it, and that is the only difference that
matters.

### Why the planted failure is this shape

An uncited answer, a refusal, or an obvious error would be found by one filter.
That proves the filter works and nothing else.

**This one carries a real citation and says the opposite of what it cites.**
Every deterministic check in this project passes it, because they all ask
whether the citation resolves, not whether it agrees. Week 6 named this
`unchecked_answer` and built a judge for it, then refused to trust the judge.

So the drill cannot be won by a flag. It has to be won by searching.

---

## 3. Cost per request, measured and improved

| | before | after |
|---|---|---|
| **Cost per request** | $0.00025401 | **$0.00006030** |
| Tokens per request | 1,316 | **320** |
| LLM calls over the whole log | 254 | **48** |

**Cost saving: 76.3%.** Cache hit rate 81.9%.

**The improvement is an answer cache.** The cheapest request is the one you
never send. Prompt caching already happens at the provider and is not ours to
tune; whether the call is made at all is.

**The fence matters more than the cache.** The key includes the model, the
prompt fingerprint and the corpus fingerprint. Change any of them and the cache
empties rather than serving six-week-old answers under a new prompt. Week 6
lost a measurement to exactly that kind of quiet staleness.

### The risk, which decides whether the saving counts

**A cache that serves the wrong answer is not a saving. It is a bug with a good
dashboard.**

| Similarity threshold | Hit rate | Saving | **Wrong answers served** |
|---|---|---|---|
| 0.5 | 81.9% | 76.3% | **0 / 48** |
| 0.7 | 81.9% | 76.3% | **0 / 48** |
| 0.8 | 81.9% | 76.3% | **0 / 48** |
| 0.9 | 81.9% | 76.3% | **0 / 45** |

**Zero wrong at every threshold, and the threshold is not the reason.**

### The near-miss that would have broken it

| | |
|---|---|
| Cached | "Getting **ERR-4032** on an invoice line. What is the fix?" |
| Asked | "Getting **ERR-4044** on an invoice line. What is the fix?" |
| Word overlap | **0.818**, above the 0.8 threshold |

**Without a code fence that is served**, and a customer gets the fix for the
wrong problem. ERR-4032 says re-map the tax code; ERR-4044 says convert to
account credit and *do not* refund.

So codes are treated as identity, not vocabulary. **Any difference in the codes
a question names blocks a similarity hit outright**, and a test proves both
halves: the near-miss is blocked, and a genuine reword still hits.

---

## 4. The failure, now a test

**R01** came out of the drill and is pinned in `evals/w11_regressions.py`.

| Check | Result |
|---|---|
| Catches the answer that actually failed | **yes** |
| Allows a correct answer | **yes** |

**Both directions matter.** A check that catches the bug but also fires on
correct answers is not a guard. It is an alarm nobody will keep.

The case records the **trace id it came from**, so six months from now the log
can answer why it exists. A regression with no provenance gets deleted by the
next person tidying up.

### Asked again, live

The current app answers it correctly:

> If the card token was dropped during migration, the refund cannot be returned
> to the original card and must be issued as account credit instead.
> [HC-4003-structured-006]

**So the bug is not present today.** The test does not prove the app is broken.
It guards against this failure returning the next time the prompt moves, which
is when regressions actually come back.

---

## 5. The 10x plan: what breaks first

At ten times this traffic, in the order it breaks:

1. **The provider's rate limit, long before anything of ours.** This project
   hit the free tier's daily cap in six of the last nine weeks. Ten times the
   traffic means hitting it at 2am instead of 4pm. **The fix is a paid tier and
   a queue, not code.**
2. **The trace log.** One JSONL file per day, read whole into memory by every
   search. At 83 traces that is 5ms. At 50,000 a day it is a problem. The fix
   is the one every team reaches for: ship the traces to something built for
   them. The shape here is already the trace-and-span shape, so the change is
   `obs/store.py` and nothing else.
3. **The answer cache.** A list scanned linearly on every lookup. Fine at
   hundreds of entries, not at hundreds of thousands.
4. **The MCP servers.** One subprocess per server per agent process, each
   loading its own copy of the embedding model. The live trace above shows
   18 seconds of start-up; at ten times the concurrency that is ten times the
   memory for the same corpus.

**What does not break: retrieval.** It is a local index over 34 chunks and has
never been the bottleneck in nine weeks of measurement.

---

## 6. What this does NOT do

- **The log is backfilled.** The questions, answers, chunk ids and token counts
  are real and come from the Weeks 7 to 10 caches. **The timestamps are
  invented**, because the caches record no wall-clock date and the drill needs
  to narrow by day. Every backfilled trace carries `backfilled: true`.
- **The hit rate is flattered.** The log replays eval runs, which asked the
  same twelve questions many times. Real support traffic is more varied, so
  **81.9% is an upper bound, not a forecast**.
- **The similarity layer contributed nothing here.** All 68 hits were exact.
  The risky half of the cache is the half this traffic never exercised, so
  "zero wrong answers" is weaker evidence than it looks.
- **The planted answer is planted.** It is marked in the log, and a test
  asserts the search never filters on that marker. The haystack is real; the
  needle was placed.
- **No rotation, no retention policy, no PII redaction.** All three are real
  production concerns. None is built.
- **`contradicts_its_citation` checks one rule**, not faithfulness in general.
  A general judge is what Week 6 built and then refused to trust.
- **One drill, one planted failure.** A second person planting a different one
  would find things this search misses.

---

## 7. Reproducing it

```bash
python -m evals.run_w11 --all     # all four parts. Free.
python -m evals.run_w11 --drill   # just the drill. Free.
python -m evals.run_w11 --cost    # cost before and after. Free.
python -m evals.run_w11 --live    # ask the pinned question again. ~2 calls.
python test_acceptance.py         # 315 checks
```

**Only `--live` spends anything.** Everything else reads the log, which is the
point of having one.

**`--all` rebuilds the log from the caches**, so a live trace made earlier is
replaced. Use `--keep-log` to append instead.

---

## 8. Files

| File | What it is |
|---|---|
| `obs/trace.py` | What is recorded, and what makes it replayable |
| `obs/store.py` | Append-only JSONL, one file per day |
| `obs/search.py` | The drill: filters, then rare-word ranking |
| `obs/backfill.py` | Real runs replayed into the log |
| `obs/plant.py` | The bad answer, and the proof it is bad |
| `obs/cache.py` | The cost improvement, and its fences |
| `obs/measure.py` | The saving and the risk, together |
| `evals/w11_regressions.py` | The failure, pinned |
| `evals/run_w11.py` | The one command |
| `results/w11_production.md` | The generated report |

---

## 9. The one-line answer to the week's question

An app that cannot find its own bad answer has not got a logging problem, it
has got a memory problem, and the fix is not more logging but the right four
fields: a time, the words, what it cited, and what each step cost.
