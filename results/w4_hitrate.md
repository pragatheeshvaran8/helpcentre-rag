# Week 4: hit-rate@3 before and after one change

- Questions: 30, one per code in the corpus
- Index: `structured` (the chunker Week 3 shipped, unchanged)
- Embedding model: `BAAI/bge-small-en-v1.5` (unchanged)
- The one change: retrieval mode `dense` -> `hybrid` (BM25 fused by RRF, rrf_k=60, BM25 k1=1.5, b=0.75)
- No LLM was called to produce this file.

## The number

| | hit-rate@3 | hit@1 | MRR | answer never in top-10 |
|---|---|---|---|---|
| **before** (dense) | **28/30** | 25/30 | 0.8889 | 0 |
| **after** (hybrid) | **30/30** | 29/30 | 0.9778 | 0 |
| change | **+2** | +4 | +0.0889 | +0 |

## Per-question record

`rank` is where the answering chunk landed, out of 10 searched. `-` means it was never found.
`arm` shows which retrieval arm surfaced it after fusion.

| Q | code | article | before hit@3 | rank | after hit@3 | rank | arm |
|---|---|---|---|---|---|---|---|
| W1 | `MIG-100` | HC-4001 | HIT | 1 | HIT | 1 | both |
| W2 | `MIG-140` | HC-4001 | HIT | 1 | HIT | 1 | both |
| W3 | `MIG-220` | HC-4001 | HIT | 1 | HIT | 1 | both |
| W4 | `MIG-310` | HC-4001 | HIT | 1 | HIT | 1 | both |
| W5 | `MIG-450` | HC-4001 | HIT | 1 | HIT | 1 | both |
| W6 | `ERR-4010` | HC-4002 | HIT | 1 | HIT | 1 | both |
| W7 | `ERR-4021` | HC-4002 | MISS | 4 | HIT | 3 | both |
| W8 | `ERR-4032` | HC-4002 | HIT | 3 | HIT | 1 | both |
| W9 | `ERR-4044` | HC-4002 | HIT | 1 | HIT | 1 | both |
| W10 | `ERR-4055` | HC-4002 | HIT | 1 | HIT | 1 | both |
| W11 | `ERR-4061` | HC-4002 | HIT | 1 | HIT | 1 | both |
| W12 | `ERR-4077` | HC-4002 | HIT | 1 | HIT | 1 | both |
| W13 | `ERR-4090` | HC-4002 | HIT | 1 | HIT | 1 | both |
| W14 | `ERR-5101` | HC-4003 | HIT | 1 | HIT | 1 | both |
| W15 | `ERR-5108` | HC-4003 | MISS | 4 | HIT | 1 | both |
| W16 | `ERR-5114` | HC-4003 | HIT | 3 | HIT | 1 | both |
| W17 | `ERR-5127` | HC-4003 | HIT | 2 | HIT | 1 | both |
| W18 | `ERR-5133` | HC-4003 | HIT | 1 | HIT | 1 | both |
| W19 | `ERR-5140` | HC-4003 | HIT | 1 | HIT | 1 | both |
| W20 | `ERR-5199` | HC-4003 | HIT | 1 | HIT | 1 | both |
| W21 | `ERR-6203` | HC-4004 | HIT | 1 | HIT | 1 | both |
| W22 | `ERR-6210` | HC-4004 | HIT | 1 | HIT | 1 | both |
| W23 | `ERR-6244` | HC-4004 | HIT | 1 | HIT | 1 | both |
| W24 | `ERR-6250` | HC-4004 | HIT | 1 | HIT | 1 | both |
| W25 | `ERR-7101` | HC-4005 | HIT | 1 | HIT | 1 | both |
| W26 | `ERR-7203` | HC-4005 | HIT | 1 | HIT | 1 | both |
| W27 | `ERR-7208` | HC-4005 | HIT | 1 | HIT | 1 | both |
| W28 | `ERR-7215` | HC-4005 | HIT | 1 | HIT | 1 | both |
| W29 | `ERR-7302` | HC-4005 | HIT | 1 | HIT | 1 | both |
| W30 | `ERR-7310` | HC-4005 | HIT | 1 | HIT | 1 | both |

## What the change did

- Fixed (2): W7, W15
- Broke (0): none
- Still failing (0): none

The still-failing list matters as much as the fixed list. Those are the
questions this change was never going to help, and they are labelled by
failure type in `w4_failures.md`.
