# Tier-1 Deflection Assistant

A support agent pastes a customer's ticket. This answers it from the help
centre, names the exact paragraph it used, and refuses when the help centre
does not hold the answer. The agent sends the reply or escalates it.

It is called a deflection assistant because the job is to settle tier-1 tickets
without a human reading the article first. It only earns that name if wrong
answers are rare and refusals are honest, which is what the measurement in this
repo is for.

> **The corpus is invented.** The 6 articles in [corpus/](corpus/) were written
> for this exercise. There is no real "BL1", no real "BL2", and no real billing
> migration. The error codes, cutover dates, plan names and API endpoints are
> all made up. They are shaped like real help-centre articles on purpose,
> because the point is to test retrieval against realistic troubleshooting
> tables. Do not read any of it as documentation for a real product.

---

## Start here

Four commands. Nothing else is needed to see this working.

```bash
pip install -r requirements.txt
cp .env.example .env          # paste an OpenRouter key into it

python app.py doctor          # is this machine ready?
python app.py index           # build the search index, once
python app.py ask "A customer's invoice is stuck on ERR-4032. What do I tell them?"
python app.py demo            # the four-part demo. Free, offline, ~20 seconds
```

`doctor` is the one to run when anything looks wrong. It checks the Python
version, the packages, the key, the corpus and the index, and for each failure
it prints the command that fixes it.

**You do not need a key for most of this.** `demo`, `eval`, `logs` and `report`
all read the log and the corpus. Only `ask` and `demo --live` call the network.

---

## The one entry point

```
python app.py <command>
```

| Command | What it does | Costs calls? |
|---|---|---|
| `doctor` | Check this machine is ready. Run it first. | no |
| `index` | Build the search index. Once, and after a corpus change. | no |
| `ask "<ticket>"` | **Answer one ticket.** This is the product. | yes, 2-4 |
| `demo` | The four-part demo. Add `--live` for a real call in part 1. | no |
| `eval` | The full test suite, 300+ checks. | no |
| `logs --trace <id>` | Reopen one past answer, with its cost per step. | no |
| `logs --find <words>` | Find a past answer from a vague complaint. | no |
| `logs --suspicious` | Answers worth a second look. | no |
| `report` | Every headline number, and the file it came from. | no |

The eleven `python -m evals.run_*` commands still exist and still work. They are
how each week's result is rebuilt. `app.py` is the door; they are the rooms.

---

## What you are looking at when you run `ask`

```
== answer ==============================================================
  ERR-4032 means the invoice line references a legacy tax code that no
  longer exists in BL2 [HC-4002-structured-004]. Re-map the line item to
  a current tax code, then reissue the invoice [HC-4002-structured-004].

  trace a4c60ee535d4   3 step(s)   3 call(s)   26.59s
  help centre: HC-4002-structured-004
```

- **`[HC-4002-structured-004]`** is a chunk id. It resolves to one paragraph in
  one article. You can read it yourself in
  [results/chunks_structured.md](results/chunks_structured.md).
- **`help centre:`** lists only the sources that really resolve.
- **`not help centre:`** appears when the answer cited a past support ticket
  instead. Those are real tickets, not inventions, but one ticket is not
  policy. The line is there so you can tell the two apart before you send the
  reply.
- **`NOT A REAL CHUNK`** in red means the answer cited something that does not
  exist. Do not send it.
- **`trace a4c60ee535d4`** is the handle. `python app.py logs --trace
  a4c60ee535d4` reopens that exact answer months later, with the time and the
  cost of every step.

---

## What runs when you ask a question

1. **Start the tool servers** listed in `mcp_servers.json` and ask each one
   what tools it has. Nothing is hard-coded. *(Week 9, MCP)*
2. **Loop:** pick a tool, run it, read the result, pick again. Budgets stop it
   running away: 6 steps, 8 calls, 120 seconds, and a repeated-action guard.
   *(Week 7)*
3. **Retrieve** with a dense vector arm and a BM25 keyword arm, fused by RRF,
   over chunks that never split a table row from its header. *(Weeks 3 and 4)*
4. **Answer** from retrieved text only, cite every sentence, and refuse when
   the facts are missing. *(Week 6)*
5. **Scan** retrieved text and the outgoing reply for injected instructions.
   *(Week 8)*
6. **Write a trace:** the question, the answer, the chunks, and one span per
   step with its own milliseconds and cost. *(Week 11)*

---

## Honest limits

Read **[KNOWN_WEAK_SPOTS.md](KNOWN_WEAK_SPOTS.md)** before you trust any number
here. It lists eight things that are wrong with this app, written before anyone
asked, with the fix for each. The short version:

- The 60 eval cases were written by one person who knew the corpus.
- The relevance judge never disagreed with itself, so that agreement figure
  means nothing. The faithfulness one is real.
- The injection guard is a pattern list, and pattern lists are beatable. The
  real containment is that the tools can only read.
- The free tier caps this at 50 model calls a day, so no sample here is large.

---

## The numbers, and where each one lives

`python app.py report` prints this table with the file beside each row.

| Week | Question | Result |
|---|---|---|
| 3 | Does a structure-aware chunker find answers inside tables better? | hit@5 tied 8/8, header-less chunks served fell **7 to 0** |
| 4 | Can one change buy back hit-rate@3? | **28/30 to 30/30**, by fusing BM25 into the vector search |
| 5 | What is actually going wrong, ranked? | retrieval **15/15**, the app still wrong **6 of 20** |
| 6 | Can a prompt fix the biggest failure? | **46.5% to 79.1%** on the 43 cases both runs scored |
| 7 | Is an agent better than a fixed workflow? | agent **12/12**, fixed workflow **8/12** |
| 8 | Does a right answer mean a right path? | outcome **12/12**, path **10/12** |
| 9 | Can tools be discovered rather than imported? | a server bolted on, **0 bytes** of the agent changed |
| 10 | Is a team of agents better than one? | single **11/12**, squad **10/12**. Kept the single agent |
| 11 | What does one request cost, and can it cost less? | cost per request **-76%**, with **0 of 48** wrong answers served |
| 12 | Can a stranger run it, and can I defend it? | this README, `app.py`, and KNOWN_WEAK_SPOTS.md |

---

# The detail, week by week

## What this measures

### Week 3: two chunking strategies

Indexed side by side, searched with the same 8 known-answer questions.

| Strategy | What it does |
|---|---|
| `baseline` | `RecursiveCharacterTextSplitter`, 1000 chars, 150 overlap. Table-blind. |
| `structured` | Parses markdown structure. A table data row is never separated from its header row. |

Held constant across both runs: the corpus, the embedding model
(`BAAI/bge-small-en-v1.5`), the distance metric (cosine), `k=5`, and the target
chunk size (1000). Only the boundary policy differs. Changing the chunker and the
embedding model in the same run would tell you nothing about which one moved the
number.

### Week 4: two retrieval modes

Same corpus, same chunker, same embedding model. 30 new questions, one per error
code, because the Week 3 set has no failures left to study.

| Mode | What it does |
|---|---|
| `dense` | Vector search alone. The Week 3 behaviour. |
| `hybrid` | The same vector search, fused with a BM25 keyword arm by RRF. |

Exactly one thing changes, and it is a single flag. No reranker, no query
rewriting, no MMR. RRF and BM25 keep their conventional constants, so no tuned
parameter sneaks in as a second change.

### Week 5: 20 traces read by hand

Nothing in the app changed this week. A measurement taken while you are also
fixing things measures nothing.

| Step | What it does |
|---|---|
| pool | 60 questions written like real agent traffic, before any of them was run |
| draw | `random.Random(5).sample(ids, 20)`. Uniform, not stratified, seed never changed |
| collect | 20 complete traces: input, every setting, every retrieved chunk, the context sent, the raw answer, every citation |
| open coding | one honest sentence per trace, written while reading, before any category existed |
| taxonomy | 3 named groups, ranked by frequency x severity, one chosen, one prediction |

The headline is a gap, not a number. **hit-rate@3 scores this sample 15 of 15
and the app was wrong 6 times out of 20.** All 6 failures happened with the
answering chunk already in the context: the model refused text that was on
screen (3), answered with no citation at all (2), or printed a refusal and then
answered underneath it (1).

## Layout

```
corpus/              the 6 new help-centre articles, with YAML front matter
config.py            every knob that could change a measurement, in one place
rag/
  documents.py       front-matter parsing -> source_file, article_id,
                     product_area, last_updated
  chunkers.py        both chunkers + the header-loss diagnostic
  ingest.py          stamps metadata + a resolvable chunk_id, indexes 6 articles
  vector_store.py    one Chroma collection per strategy
  retriever.py       search, with an optional product_area pre-filter
  keyword.py         BM25 over the same chunks (week 4, no new dependency)
  hybrid.py          RRF fusion of the dense and keyword arms (week 4)
  answerer.py        grounded generation with a FORCED refusal
  term.py            ANSI colour, off automatically when piped
evals/
  questions.py       the 8 week-3 questions, committed before any retrieval code
  run_search_eval.py hit-in-top-5 for both strategies + the search-only dump
  run_filter_demo.py unfiltered vs filtered result lists
  run_generation.py  3 cited answers + 3 refusals
  run_bonus.py       the precision/completeness tension
  dump_chunks.py     makes every chunk_id resolvable and clickable
  w4_questions.py    the 30 week-4 questions, one per error code
  w4_measure.py      hit-rate@3 before and after the one change
  w4_failures.py     labels each failure A (wrong doc) or B (wrong answer)
  w5_questions.py    the 60-question traffic pool, written before any trace ran
  w5_sample.py       the seeded draw of 20, and the audit of what it picked
  w5_trace.py        what a complete trace is, and the pass/fail rule
  w5_collect.py      runs the 20 traces, resumable, writes them to be read
  w5_notes.py        one hand-written sentence per trace, written before grouping
  w5_taxonomy.py     the named groups, the ranking, the target, the prediction
  run_all.py         every stage in one process
ask.py               interactive terminal client
test_acceptance.py   asserts every claim the write-ups make
results/             all generated output, committed
```

Weeks 7 to 12 added three more directories and two files at the root:

```
app.py               THE ENTRY POINT. Every command below is a subcommand of it
demo.py              the four-part demo: a run, a failure, a number, what next
KNOWN_WEAK_SPOTS.md  eight things wrong with this app, and the fix for each
agent/
  loop.py            the agent loop: thought, tool, observation, repeat
  tools.py           the three tools, and what their descriptions have to say
  budget.py          steps, calls, seconds, and the repeated-action guard
  guard.py           injection patterns, fencing, and output validation
  mcp_client.py      JSON-RPC over stdio, hand-written, no framework
  toolbox.py         discovers tools from mcp_servers.json at start-up
  meter.py           tokens and cost, taken from the provider's own report
  squad.py           agent cards, task lifecycle, manager and two specialists
mcp_servers/         the servers the agent discovers, including a hostile one
obs/
  trace.py           a trace and its spans, with the config pinned at run time
  store.py           one JSONL file per UTC day
  search.py          the support drill: find one answer from a vague complaint
  cache.py           the answer cache, and the config fence around it
  measure.py         the saving and the risk, measured together
  plant.py           the planted bad answer the drill has to find
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env      # add an OpenRouter key
```

Only generation needs the key. Ingest and the search-only evaluation run fully
offline on a local embedding model.

Keep `.env` minimal. It should hold the API key and nothing else. Every
retrieval knob belongs in `config.py`, where the write-up can point at it. A
stray `TOP_K=4` in a copied `.env` silently turned the first run of this project
into a top-4 measurement.

## Run it

The embedding model contacts the HuggingFace Hub on every load, even when the
model is already cached. If the network is slow that call blocks for minutes.
After the first successful run, pin it offline:

```bash
export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1     # PowerShell: $env:HF_HUB_OFFLINE=1
```

```bash
python -m rag.ingest              # index the 6 new articles, both strategies
python -m evals.run_search_eval   # the two X/8 numbers + full search dump
python -m evals.run_filter_demo   # product_area filter changes top-1
python -m evals.run_generation    # 3 cited answers, 3 refusals
python -m evals.run_bonus         # precision vs completeness
python -m evals.dump_chunks       # resolvable chunk files
```

Week 4:

```bash
python -m evals.w4_measure        # hit-rate@3 before/after, no API key needed
python -m evals.w4_failures       # label each failure A or B, needs an API key
```

Week 5:

```bash
python -m evals.w5_sample         # show the draw and what it picked, no API key
python -m evals.w5_collect        # collect the 20 traces, needs an API key
python -m evals.w5_taxonomy       # rebuild the taxonomy, no API key needed
```

`w5_collect` is resumable. Every trace is appended to `results/w5_traces.jsonl`
the moment it completes, a re-run skips what is settled and retries only what
errored, and calls are spaced 4 seconds apart to stay under the free tier's
20-per-minute cap.

Or everything in one process, which is much faster because the embedding model
loads once:

```bash
python -m evals.run_all                      # weeks 3, 4 and 5
python -m evals.run_all --week 5             # week 5 only
python -m evals.run_all --skip-generation    # no API key needed
```

Resolve any citation straight out of the vector store:

```bash
python -m evals.dump_chunks --resolve HC-4002-structured-004
```

## Test it

```bash
python test_acceptance.py                    # 67 checks, no API key needed
python test_acceptance.py --with-generation  # 85 checks, adds 6 LLM calls
```

**The 67-check run is green. The generation run is not, and that is a real
finding rather than a broken setup.** On the current free model,
`--with-generation` fails 3 of 85 checks, all of them Q3, and all one cause: the
model answers correctly and emits no `[chunk_id]` at all. That is the problem
Week 5 ranked first, "answers with nothing you can check". It is intermittent:
the same question asked through `ask.py` produced a properly cited answer. See
[results/w5_results.md](results/w5_results.md) section 5.

Exits non-zero on any failure. Each check maps to a claim in a write-up that a
grader could challenge:

- all 6 articles load with complete front matter
- every chunk carries `source_file`, `article_id`, `product_area`, `last_updated`, `chunk_id`
- every `chunk_id` resolves back out of the store, and a made-up one does not
- **no structure-aware chunk holds table rows without a header row**
- all 8 known-answer questions hit in top-5, on both strategies
- the `product_area` filter changes top-1, and promotes chunks from outside the unfiltered top-5
- the 3 cited answers cite chunks that really contain the claim
- the 3 out-of-corpus questions are refused by the model, with the gate off

Week 4:

- the BM25 tokeniser keeps `err-7208` as one token, and also emits the parts
- BM25 alone ranks the `ERR-7208` chunk first
- a rare code outweighs a common word on IDF (3.150 against 0.105)
- **hybrid strictly improves hit-rate@3, and breaks nothing dense already found**
- both modes share one embedding model, and RRF and BM25 use untuned defaults
- every Week 4 answer string is verbatim in the corpus

Week 5:

- the pool is 60, every required string is verbatim, and **every requirement is
  satisfiable by a single chunk**, so no question can invent a failure
- the draw is plain `random.sample` with seed 5, reproducible, and a different
  seed gives a different sample
- all 20 traces are complete, none left in the error state, none stale against
  the current corpus hash and prompt hash
- **every stored grade can be rebuilt from the trace alone**, which is what makes
  a trace replayable rather than merely long
- every trace has a hand-written note, and **no note names a group**, so the
  notes provably came before the categories
- every failing trace is in exactly one group, and no passing trace is in any
- the ranking really is frequency times severity, and every predicted metric
  says what would falsify it

## Ask it your own questions

The scripts above run a fixed set of questions and write files. `ask.py` is the
interactive terminal client: type a question, see exactly what retrieval
returned, and see whether the model answers it or refuses.

```bash
python ask.py                         # interactive
python ask.py --search-only           # retrieval only, no LLM, no API key
python ask.py "what is ERR-4032?"     # one question, then exit
```

Inside the session:

| Command | Effect |
|---|---|
| `:strategy baseline` | switch index (`structured` or `baseline`) |
| `:mode dense` | switch retrieval (`hybrid` or `dense`) |
| `:area api` | filter to a product_area |
| `:area off` | clear the filter |
| `:k 3` | change how many chunks are retrieved |
| `:search on` | retrieval only, skip the LLM |
| `:quit` | leave |

### Reading the output

Output is colour-coded, and switches to plain text automatically when piped or
redirected, so the generated files stay clean.

| What you see | Meaning |
|---|---|
| `== ANSWER ==` in green | The model answered from the corpus |
| `== REFUSED by the model ==` in red | Nothing retrieved could answer it |
| `[HC-4002-structured-004]` in cyan | A citation inside the answer |
| `OK resolves` | That chunk_id exists in the index |
| `FAIL does not resolve` | A fabricated citation. Should never happen |
| `<<< USED IN ANSWER` in green | **This is the chunk the answer came from** |
| `[table+header]` in green | The chunk kept its table column header |
| `[HEADER-LESS TABLE]` in red | The chunk lost its header. The Week 3 defect |
| `[BM25 ONLY]` in magenta | Only the keyword arm found this. The Week 4 fix working |

`<<< USED IN ANSWER` is the one to look for. Retrieval returns five chunks; that
marker tells you which of them the answer was actually built from. It is often
not the top-ranked one.

Force colour on or off with `--color` / `--no-color`, or the `NO_COLOR` and
`FORCE_COLOR` environment variables.

Run the same question under `:strategy baseline` and `:strategy structured` to
see `HEADER-LESS TABLE` appear and disappear.

### One note on re-running

Some chunks score identically to four decimal places. Chroma does not guarantee
a stable order between exact ties, so re-running can swap two adjacent results.
Every reported number is unaffected: hit rates, MRR, and the header-less counts
are all identical across runs.

## Time reality

`rag/ingest.py` indexes the 6 new articles only. There is no historical corpus in
this index and nothing else is re-indexed. A full rebuild of both collections
takes seconds. The measurement is the deliverable; the ingest is plumbing.
