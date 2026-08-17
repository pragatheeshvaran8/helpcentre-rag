# helpcentre-rag

Week 3 Practical, Task Set A. Ingest a 6-article help-centre drop about a billing
migration, then measure whether the chunker can actually find the answer inside a
troubleshooting table.

> **The corpus is invented.** The 6 articles in [corpus/](corpus/) were written
> for this exercise. There is no real "BL1", no real "BL2", and no real billing
> migration. The error codes, cutover dates, plan names and API endpoints are all
> made up. They are shaped like real help-centre articles on purpose, because the
> point of the exercise is to test a chunker against realistic troubleshooting
> tables. Do not read any of it as documentation for a real product.

The deliverable is **[results/results.md](results/results.md)**. Everything else
in this repo exists to produce it.

## What this measures

Two chunking strategies, indexed side by side, searched with the same 8
known-answer questions.

| Strategy | What it does |
|---|---|
| `baseline` | `RecursiveCharacterTextSplitter`, 1000 chars, 150 overlap. Table-blind. |
| `structured` | Parses markdown structure. A table data row is never separated from its header row. |

Held constant across both runs: the corpus, the embedding model
(`BAAI/bge-small-en-v1.5`), the distance metric (cosine), `k=5`, and the target
chunk size (1000). Only the boundary policy differs. Changing the chunker and the
embedding model in the same run would tell you nothing about which one moved the
number.

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
  answerer.py        grounded generation with a FORCED refusal
evals/
  questions.py       the 8 questions, committed before any retrieval code
  run_search_eval.py hit-in-top-5 for both strategies + the search-only dump
  run_filter_demo.py unfiltered vs filtered result lists
  run_generation.py  3 cited answers + 3 refusals
  run_bonus.py       the precision/completeness tension
  dump_chunks.py     makes every chunk_id resolvable and clickable
results/             all generated output, committed
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

Resolve any citation straight out of the vector store:

```bash
python -m evals.dump_chunks --resolve HC-4002-structured-004
```

## Test it

```bash
python test_acceptance.py                    # 20 checks, no API key needed
python test_acceptance.py --with-generation  # 36 checks, adds 6 LLM calls
```

Exits non-zero on any failure. Each check maps to a claim in `results.md` that a
grader could challenge:

- all 6 articles load with complete front matter
- every chunk carries `source_file`, `article_id`, `product_area`, `last_updated`, `chunk_id`
- every `chunk_id` resolves back out of the store, and a made-up one does not
- **no structure-aware chunk holds table rows without a header row**
- all 8 known-answer questions hit in top-5, on both strategies
- the `product_area` filter changes top-1, and promotes chunks from outside the unfiltered top-5
- the 3 cited answers cite chunks that really contain the claim
- the 3 out-of-corpus questions are refused by the model, with the gate off

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
| `[HEADER-LESS TABLE]` in red | The chunk lost its header. The defect being measured |

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
