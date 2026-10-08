# EXE02 — Graded relevance and nDCG

**Concept:** three questions about a ranked list, three metrics with fixed
names:

| Metric              | Question it answers |
|---------------------|---------------------|
| `section_recall@k`  | is a chunk of the right section in the top k? (R@k of unit 03) |
| `evidence_recall@k` | is a chunk that holds the facts in the top k? |
| `nDCG@k`            | how well is the top k ordered? |

Why graded relevance: the error codes, troubleshooting and start-up sections
are split into two chunks. Only one of the two holds the code you asked about.
So a chunk gets a **gain**:

```text
2  right section, and every expected fact   (an evidence chunk)
1  right section, without the facts
0  anything else
```

nDCG compares the gains of your top k with the best order possible:

```text
DCG@k  = sum over positions i = 1..k of (2^gain_i - 1) / log2(i + 1)
nDCG@k = DCG@k(your order) / DCG@k(ideal order)
```

A gain-2 chunk at rank 1 is worth 3; at rank 2 it is worth 3 / log2(3) ≈ 1.89.
nDCG rewards putting the best chunk first, not only having it in the list.

## Task

Implement `gain(chunk, question)` and `ndcg_at_k(gains, ideal, k)` in
`exe02.py`.

```bash
uv run python exercises/exe02-ndcg/check.py
```

## Run, one step at a time

### 1. Same recall, better order

```bash
uv run python exercises/exe02-ndcg/exe02.py --case 3
```

"The Ibis R-26 shows E-6230. What should I check?" The table shows the gains
of the top 3 before and after reranking, and nDCG@3 for both.

Measured: gains `0 2 0` (nDCG@3 0.387) became `2 2 0` (nDCG@3 1.000). The
evidence was in the top 3 before and after, so `evidence_recall@3` is the
same ("same" in the table). Only the order improved, and only nDCG sees it.

### 2. The dev set

```bash
uv run python exercises/exe02-ndcg/exe02.py
```

Read the "evidence_recall@3" column ("same" or "changed") next to the two
nDCG columns. The last column compares your nDCG with the library's.

Measured (`nomic-embed-text`, N = 20, MiniLM), on the 33 answerable
questions:

- 7 questions say "changed": the reranker brought an evidence chunk into
  the top 3 that was not there (for example s04, gains `0 0 0` → `2 1 0`).
- Among the questions with the "same" recall, four show nDCG moving:
  s03 0.387 → 1.000 and s17 0.387 → 0.613 (the evidence moved up), but s19
  0.629 → 0.556 (`0 2 2` → `2 0 0`) and s25 1.000 → 0.826 (`2 1 0` → `2 0 0`)
  went **down**: the reranker put an evidence chunk first but pushed a second
  gain-2 or a gain-1 chunk out of the top 3. Recall cannot see that.
- s07 and s28 stay at `0 0 0`: no evidence among the candidates for s07, and
  for s28 the evidence stays at rank 5.
