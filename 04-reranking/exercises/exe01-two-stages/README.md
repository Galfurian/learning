# EXE01 — Two stages

**Concept:** retrieval and reranking are two stages with two jobs.

- The **first stage** scores every chunk alone (one vector per chunk,
  computed without the question). It is cheap, so it can look at all 600
  chunks.
- The **reranker** reads the question and one candidate together. It is
  expensive, so it looks only at the N candidates of the first stage.

The reranker reorders and cuts. It never finds anything new: every hit it
returns came from the first stage, and each one keeps its first-stage rank so
you can see how far it moved.

## Task

Implement `rerank(question, hits, score, k)` in `exe01.py`: score the hits,
sort by score (highest first, equal scores in the first-stage order), keep
k, and return new hits with `rank`, `kind`, `rerank_score` and `first_rank`
set. The comment in the file lists every rule.

```bash
uv run python exercises/exe01-two-stages/check.py
```

## Run, one step at a time

### 1. A reranker without a model

```bash
uv run python exercises/exe01-two-stages/exe01.py --case 4 --reranker fake
```

"What does E-4210 mean on the Kestrel LX-69?" The FakeReranker scores a
candidate by the share of the question's words it contains. Look at the
"from" column: your `rerank()` moved the chunks.

Measured: `laser1-errors-2` (the evidence, gain 2) moved from rank 6 to rank
1, with a score of 0.75.

### 2. The same question with MiniLM

```bash
uv run python exercises/exe01-two-stages/exe01.py --case 4
```

Measured: the evidence moved from 6 to 1 again (relevance score 6.59), the
other chunk of the same section from 4 to 2, and a chunk of a sibling machine
(`laser5-errors-1`) from 11 to 3. The two rerankers agree on rank 1 here;
the scores are on different scales.

### 3. The dev set

```bash
uv run python exercises/exe01-two-stages/exe01.py --eval
```

Look at the last line: "Chunks your rerank() added that the first stage never
returned: none". That is the rule of this unit, checked on 37 questions.

Measured (`nomic-embed-text`, N = 20, MiniLM):

|               | `section_recall@3` | `evidence_recall@1` | `evidence_recall@3` | MRR   | `nDCG@3` |
|---------------|--------------------|---------------------|---------------------|-------|----------|
| first stage   | 0.758              | 0.636               | 0.727               | 0.713 | 0.661    |
| your rerank() | 0.939              | 0.909               | 0.939               | 0.930 | 0.866    |

The second row is the same as EXE00 `--eval`: same candidates, same reranker,
your code instead of the library's.
