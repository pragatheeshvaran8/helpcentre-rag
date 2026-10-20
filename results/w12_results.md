# Week 12 — Ship it and defend it

The task was to turn eleven weeks of separate exercises into one app a stranger
can run, package it, find what breaks at the seams, and build a demo that shows
a real failure rather than a perfect run.

**The headline: the project had eleven front doors and now has one.** Closing
the seams between them found two real bugs, both described below, both fixed,
both now pinned by a test.

**The acceptance suite is green for the first time in the project: 368 checks,
0 failures.** It was 316 with one long-standing red at the start of this week.

---

## 0. What this week produced

| | |
|---|---|
| The single entry point | `app.py` |
| The four-part demo | `demo.py` |
| The stranger's guide | `README.md`, rewritten from the front |
| The honest limits | `KNOWN_WEAK_SPOTS.md` |
| 52 new acceptance checks | `test_acceptance.py`, now 368 |

---

## 1. The integration problem, stated plainly

Before this week, running anything meant knowing which of these to type:

```
evals/run_all.py        evals/run_evals.py      evals/run_race.py
evals/run_w8.py         evals/run_w9.py         evals/run_w10.py
evals/run_w11.py        evals/run_search_eval.py  evals/run_generation.py
evals/run_filter_demo.py  evals/run_bonus.py
ask.py                  test_acceptance.py
```

**Eleven `run_*` commands plus two more.** That is fine for a course, where the
person typing wrote all of them. It is useless to anyone else, because nothing
tells a newcomer which one to start with.

`app.py` is now the one door:

| Command | What it does | Costs calls? |
|---|---|---|
| `python app.py doctor` | Check the machine is ready. Run it first. | no |
| `python app.py index` | Build the search index. | no |
| `python app.py ask "<ticket>"` | **Answer one ticket.** The product. | yes, 2-4 |
| `python app.py demo` | The four-part demo. | no |
| `python app.py eval` | 368 checks. | no |
| `python app.py logs --trace <id>` | Reopen one past answer. | no |
| `python app.py logs --find <words>` | The support drill. | no |
| `python app.py report` | Every number, and its file. | no |

**Nothing was deleted and nothing was rewritten.** Every `run_*` command still
works and still rebuilds its week's result. A test asserts `app.py` holds no
prompt of its own, no model client of its own, and no retrieval of its own, so
the thing the demo runs is the thing the evals scored.

---

## 2. The two bugs the seams were hiding

### Bug 1: the test suite called twenty good traces stale

**What it looked like.** This line had been red since Week 6:

```
FAIL  no trace is stale against the current corpus and prompt  ['T01', 'T02', 'T03']
```

**What was actually wrong.** The check asked "does every trace's prompt hash
match the prompt that is active right now?" The Week 5 traces were recorded
under prompt v1. Week 6 made v2 the active prompt. So the check went red, and
it stayed red for six weeks, and I had learned to read past it.

**Why that is the wrong question.** A trace recorded under v1 is not broken. It
is a record of what v1 did. It stays replayable for as long as v1 is still in
the codebase and the corpus has not moved under its chunk ids. Those are the
two things that genuinely destroy a trace, and neither of them had happened.

**The fix.** `known_prompt_fingerprints()` in `evals/w5_trace.py` returns every
prompt version the codebase still holds. The check now asks the two real
questions separately:

```
PASS  no trace was taken against a different corpus
PASS  every trace's prompt is still in the codebase, so it can be replayed
INFO  w5 traces vs the active prompt  0/20 on the current prompt;
      the rest are v1 records and replay against v1
```

**The lesson is about the red line, not the code.** A failing check that is
always failing stops being a check. It becomes wallpaper. Six weeks is a long
time to walk past the same red word.

---

### Bug 2: the app printed policy and anecdote in the same brackets

**How it was found.** By running the new entry point on a real ticket, which is
the whole point of having one. The answer ended:

> ...so if re-mapping alone does not hold, escalate to Billing Ops
> **[SUP-2041][SUP-2114]**.

And the summary line underneath said:

```
sources: HC-4002-structured-004
```

**What is wrong with that.** Two things, and the second is the bad one.

- `SUP-2041` and `SUP-2114` are **real past support tickets**, served by the
  ticket-history MCP server. The model did not invent them.
- But they are printed in **exactly the same brackets** as
  `[HC-4002-structured-004]`, which is help-centre policy. The person about to
  send that reply cannot tell a documented rule from one thing that happened to
  one customer once.

**And the citation check never saw them.** It matches only the
`HC-xxxx-strategy-nnn` shape. A `[SUP-2041]` is not an unresolved citation to
it. It is nothing at all, and nothing is what got reported.

**The fix.** `unchecked_marks()` in `app.py` finds every bracket mark in the
answer that is not a help-centre chunk id, and the output now separates them:

```
help centre: HC-4002-structured-004
not help centre: SUP-2041, SUP-2114
Those are past tickets, not policy. One ticket is not a rule.
Check anything they support before you send it.
```

**It does not strip them.** A past ticket is often the most useful line in the
reply. The fix is labelling, not removal.

**Why this was invisible for five weeks.** Every eval scores the HC citations
and ignores everything else. The tool that serves past tickets was added in
Week 9 and nothing ever asked what happened to its output downstream. **A seam
is exactly the place where each side is individually correct.**

---

## 3. The demo, and why part 1 is free by default

`python app.py demo` runs four parts:

| Part | Shows | Costs |
|---|---|---|
| 1. A real run | one ticket, every step, its milliseconds and its cost | free (replay) |
| 2. A real failure | a wrong answer every cheap check passed | free |
| 3. A number that improved | before, after, and the caveat | free |
| 4. What is next | the weak spots, named | free |

`--live` makes part 1 ask a real question instead of replaying one.

**The default is a replay on purpose.** The provider allows 50 free calls a
day. A demo that needs the network can fail in front of a room for a reason
that has nothing to do with the work. `--live` exists because a replay alone
would be a fair thing to doubt.

**Two things part 1 learned from a bad first attempt:**

- It skips the planted refund ticket, because part 2 is entirely about that
  one. Opening on it made the app look like it knew a single question.
- It prefers a trace that was really metered. Some traces in the log were
  rebuilt from cached runs and carry no token counts, and a cost table of zeros
  immediately before the part that defends the cost numbers is the worst
  possible ordering.

---

## 4. Part 2: the failure worth showing

The demo does not describe the failure. It runs the detector, live, on the
exact answer that failed.

**The complaint, as forwarded.** No ticket number, no date, no wording:

> Finance flagged something from about a week ago. Someone asked us about a
> refund where the card had been lost in the migration, and we apparently told
> them it would go back on the original card.

**The answer that was found:**

> Yes. Refunds are issued back to the original payment method, so this one will
> be returned to the customer's original card automatically once the credit is
> approved [HC-4003-structured-006].

**Every cheap check passed it:**

| Check | Result |
|---|---|
| the citation HC-4003-structured-006 resolves | yes |
| every sentence names a source | yes |
| nothing answerable was refused | yes |

**Three green checks, and the answer is still wrong.** The chunk it cites says
the refund *cannot* go back to the card and must be account credit.

**A citation proves a chunk exists. It does not prove the answer agrees with
it.** That is the single most useful sentence this project produced.

**What catches it now:**

```
contradicts_its_citation()                           FIRES
regression R01 on the BAD answer                     caught
  missing: 'account credit'
  must not say: "returned to the customer's original card"
regression R01 on a GOOD answer                      passes
```

**The last line matters as much as the first.** A check that fails everything
is not a check. This one separates the two answers.

**And the live app now gets it right.** Run today, through the new entry point:

> No, you cannot refund to the card. If the card token was dropped during
> migration, the refund cannot be returned to the card and must be issued as
> account credit instead. [HC-4003-structured-006]

---

## 5. Defending the numbers

Two numbers, each with what it is not.

### Accuracy: 46.5% to 79.1%

| | passed | rate |
|---|---|---|
| prompt v1 (before) | 20/43 | 46.5% |
| **prompt v2 (after)** | **34/43** | **79.1%** |

**Why 43 and not 60.** 43 of the 60 cases were scored under both prompts. The
rest hit the daily call cap on one side or the other. Scoring a case that one
run never reached would make the gain look bigger than it is. **The denominator
is the first thing a sceptical reviewer should ask about, and this project got
it wrong three separate times before settling on one shared helper.**

**What changed.** One rule. v1 said *a partial answer is a refusal*, so the
model refused whenever the wording looked unfamiliar. v2 says *never refuse
because of how the question is worded*, and names four traps. False refusals
were 21 of the failures in the before run.

**What it does not tell you.** 60 cases, written by one person who had read the
corpus. A different set moves this number, and I cannot say by how much.

### Cost: down 76.3% per request

| | |
|---|---|
| cost per request | **-76.3%** |
| cache hit rate on replayed traffic | 81.9% |
| wrong answers the cache served | **0 of 48** |

**The third row is the one to defend.** A cache that serves a stale or
near-miss answer is not a saving; it is a bug with a good dashboard. The saving
was measured next to its risk, at four match thresholds, and both were reported
together.

**What it does not tell you.** The model is free, so the money figure is a
published rate applied to real token counts, not a bill. 81.9% is a hit rate on
replayed traffic, which is a ceiling rather than a forecast. And the cache
matches on word overlap, so a negated near-duplicate is the shape that would
slip through. My traffic did not contain one.

---

## 6. The fresh-eyes test

The README was a Week 3-4-5 document. A stranger opening it was told about
chunking strategies before being told how to run anything.

It now opens with four commands, in order, with the one that costs money marked
as costing money. `doctor` comes first and prints the fixing command beside
every failure:

```
== doctor ==============================================================
  ok   python 3.10 or newer                   3.13.15
  ok   dependencies installed                 chromadb, langchain, mcp
  ok   a .env file with an API key            key ending 9860
  ok   model chosen                           poolside/laguna-s-2.1:free
  ok   corpus present                         6 articles
  ok   search index built                     34 chunks

  Ready. Try: python app.py ask "What is the fix for ERR-4032?"
```

A test asserts the README contains each of the six setup steps, says which
commands cost calls, links the weak spots, and explains the output rather than
only listing commands.

**One thing a test cannot check: whether a stranger actually succeeds.** That
needs a stranger. The checks make failure unlikely, not impossible.

---

## 7. A small fix with a disproportionate effect

Three separate commands used to print a hub warning and a progress bar in the
middle of their output, because loading the embedding model writes to stderr
and takes 13 to 40 seconds. Twice during this project that silence was read as
a hang and interrupted with Ctrl+C.

`_warm_the_index()` now loads it first, says so, and holds stderr for the
duration. **The captured text is kept, not discarded**: if the load fails, the
message that explains the failure is printed. Swallowing the one line that
explains a crash would be worse than the noise it was hiding.

```
  loading the corpus index... ready
```

---

## 8. What this week does NOT claim

- **One entry point is not one codebase.** `app.py` unifies the surface. The
  eleven `run_*` commands still exist, and someone rebuilding a week's result
  still has to know which one.
- **368 green checks is not proof of correctness.** Most of them assert that a
  write-up matches the data behind it. That stops me from claiming things the
  files do not say. It does not stop the files from being wrong together.
- **The two bugs found this week were found by looking.** There was no
  systematic seam audit. A different hour of poking would have found different
  ones, which is a reason to believe there are more.
- **Nothing here was tested by a real stranger.** See section 6.
- **No number in this project comes from a large sample.** 50 free calls a day
  shaped every measurement in it.

---

## 9. Reproducing it

```bash
python app.py doctor          # is this machine ready?
python app.py index           # build the index, once
python app.py demo            # the four parts. Free, offline
python app.py demo --live     # part 1 asks a real question. 2-4 calls
python app.py eval            # 368 checks. Free
python app.py report          # every number, and the file it came from
python app.py ask "Customer hit ERR-4044 on an invoice. What do I do?"
```

---

## 10. Files

| File | What it is |
|---|---|
| `app.py` | The single entry point, and the policy-vs-anecdote fix |
| `demo.py` | The four-part demo |
| `KNOWN_WEAK_SPOTS.md` | Eight things wrong with this app, with fixes |
| `README.md` | The stranger's guide, rewritten from the front |
| `evals/w5_trace.py` | `known_prompt_fingerprints()`, the stale-trace fix |
| `test_acceptance.py` | 368 checks, 52 of them new this week |

---

## 11. The one-line answer to the week's question

Putting one door on eleven rooms took an afternoon and found two bugs that
eleven weeks of per-week testing had each individually passed, which is the
best argument I have for why integration is its own piece of work.
