# EXE05 — Candidate depth

**Concept:** the reranker sees only the first N candidates. That gives a
**ceiling**:

```text
evidence_recall@1 after reranking  <=  evidence_recall@N of the first stage
```

If the evidence chunk is not among the N candidates, no reranker can put it
first. The ceiling holds for presence metrics (the two recalls). MRR and nDCG
can still change at the same recall, because they measure the order.

A larger N raises the ceiling and costs more: the reranker scores every one
of the N candidates (EXE06).

## Task

Implement `depth_curve(questions, candidates, rerank_fn, depths, ideals)` in
`exe05.py`: for every depth N, cut the candidates to N, rerank them, and
return the ceiling, the first stage's `evidence_recall@1`, the reranked
`evidence_recall@1` and `nDCG@3`.

```bash
uv run python exercises/exe05-depth/check.py
```

## Run, one step at a time

### 1. The curve for a weak and a very weak first stage

```bash
uv run python exercises/exe05-depth/exe05.py
```

Two tables: `nomic-embed-text`, then the FakeEmbedder; MiniLM reranks; N = 5,
10, 20, 50. Read "reranked @1" next to "ceiling" on every row.

Measured:

| `nomic` | ceiling | first stage @1 | reranked @1 | `nDCG@3` |
|---------|---------|----------------|-------------|----------|
| N = 5   | 0.758   | 0.636          | 0.727       | 0.685    |
| N = 10  | 0.909   | 0.636          | 0.879       | 0.825    |
| N = 20  | 0.970   | 0.636          | 0.909       | 0.866    |
| N = 50  | 1.000   | 0.636          | 0.939       | 0.896    |

| `fake`  | ceiling | first stage @1 | reranked @1 | `nDCG@3` |
|---------|---------|----------------|-------------|----------|
| N = 5   | 0.697   | 0.455          | 0.697       | 0.673    |
| N = 10  | 0.848   | 0.455          | 0.848       | 0.794    |
| N = 20  | 0.970   | 0.455          | 0.970       | 0.891    |
| N = 50  | 1.000   | 0.455          | 0.970       | 0.908    |

- With the FakeEmbedder, up to N = 20 the reranker reaches the ceiling
  exactly: whenever the evidence is among the candidates, MiniLM puts it
  first. The limit is the first stage, not the reranker.
- With `nomic`, the reranker gets close to the ceiling but not to it: at
  N = 50 the ceiling is 1.000 and the reranked value 0.939. Two evidence
  chunks are among the 50 and still lose to a distractor.
- "first stage @1" does not depend on N: the first stage's top 1 is the same
  at every depth.

### 2. BM25: N is not always N

```bash
uv run python exercises/exe05-depth/exe05.py --first-stage bm25
```

BM25 returns only chunks that share a token with the question. For s05 ("What
is PN-X2R-919-A?") it returns **one** candidate at every depth: the only
chunk that contains the token `pn-x2r-919-a`. The ceiling uses what came
back.

Measured: the ceiling is 0.939 at N = 5 and 1.000 from N = 10; the reranked
value stays at 0.970 from N = 10 on.

### 3. A strong first stage: more candidates, more distractors

```bash
uv run python exercises/exe05-depth/exe05.py --first-stage gemma
```

Measured: the ceiling is already 1.000 at N = 5. The reranked
`evidence_recall@1` is 0.970 at N = 5, 10 and 20, and drops to 0.939 at
N = 50; `nDCG@3` drops from 0.912 to 0.896. With a first stage this good, a
larger N only gives the reranker more chances to promote a wrong chunk.
