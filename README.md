# helpcentre-rag

Week 3 Practical, Task Set A. Ingest a 6-article help-centre drop about a billing
migration, then measure whether the chunker can actually find the answer inside a
troubleshooting table.

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

Retrieved chunks are flagged. `table+header` means the chunk kept its column
header. `HEADER-LESS TABLE` means it did not, which is the defect the whole
measurement is about. Run the same question under `:strategy baseline` and
`:strategy structured` to see the difference directly.

## Time reality

`rag/ingest.py` indexes the 6 new articles only. There is no historical corpus in
this index and nothing else is re-indexed. A full rebuild of both collections
takes seconds. The measurement is the deliverable; the ingest is plumbing.
