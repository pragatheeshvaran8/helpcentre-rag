# Hit-in-top-5, same 8 questions, both chunking strategies

- Questions: 8
- k = 5 (top-5)
- Embedding model: `BAAI/bge-small-en-v1.5` (IDENTICAL for both runs)
- Distance: cosine; target chunk size: 1000
- No relevance threshold is applied. A miss is a real retrieval miss.

## Per-question record

| Q | Type | Expected article | baseline hit | rank | structured hit | rank |
|---|---|---|---|---|---|---|
| Q1 | table_row | HC-4002 | HIT | 2 | HIT | 3 |
| Q2 | table_row | HC-4003 | HIT | 1 | HIT | 1 |
| Q3 | table_row | HC-4005 | HIT | 1 | HIT | 1 |
| Q4 | table_row | HC-4006 | HIT | 1 | HIT | 1 |
| Q5 | table_row | HC-4004 | HIT | 1 | HIT | 1 |
| Q6 | prose | HC-4001 | HIT | 1 | HIT | 1 |
| Q7 | prose | HC-4003 | HIT | 1 | HIT | 1 |
| Q8 | prose | HC-4006 | HIT | 1 | HIT | 1 |

## The two numbers

| Chunking strategy | hit-in-top-5 |
|---|---|
| baseline (RecursiveCharacterTextSplitter, 1000/150) | 8/8 |
| structured (table-row aware) | 8/8 |

## Secondary metrics, same run, same 8 questions

hit-in-top-5 saturates on a 6-article corpus, because top-5 is about
15% of the whole index. These come from the identical retrieval run.

| Metric | baseline | structured |
|---|---|---|
| hit-in-top-5 | 8/8 | 8/8 |
| hit-in-top-1 | 7/8 | 7/8 |
| mean reciprocal rank | 0.9375 | 0.9167 |
| chunks delivered into context | 40 | 40 |
| of those, header-less table chunks | 7 | 0 |
| questions given a header-less chunk | 4/8 | 0/8 |

## Near misses

A near miss means the right article was retrieved but the chunk could
not answer the question. That is the table-splitting failure, and it is
a different fault from retrieving the wrong article.

| Q | strategy | near miss |
|---|---|---|
