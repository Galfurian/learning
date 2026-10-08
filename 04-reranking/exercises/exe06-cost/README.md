# EXE06 — Cost versus quality

**Concept:** why the architecture "retrieve, then rerank" exists. A reranker
reads the question and one passage together, one pair at a time. Scoring all
600 chunks that way is too slow; scoring N candidates is affordable. N trades
quality (the ceiling of EXE05) against cost (this exercise).

## Where the times come from

- **MiniLM and bge** are timed in this run, on the local CPU: pinned
  revision, `max_length` 512, 4 threads, 3 warm-up pairs not timed, batch 1,
  model load reported apart. The cost per question is measured on 8 dev
  questions.
- **tev1** is timed by `scripts/measure_tev1_cpu.py`, on the local CPU, with
  only tev1 loaded and BM25 as the first stage (no embedding model in
  memory), on a few questions only: tev1 on a CPU takes seconds per request.
  The table scales its cost per pair to N.
- GPU times (EXE04 on a lab machine) are not used here: they are not CPU
  costs.

Measured on the local CPU (WSL, no GPU):

| reranker              | cost                                      | load |
|-----------------------|-------------------------------------------|------|
| MiniLM, batch 1       | 12.9–20.0 ms per pair (three runs)        | 0.1–0.2 s |
| MiniLM, batch 8       | 10.3–23.7 ms per pair (three runs)        |      |
| tev1 mode A (N = 10)  | 30 requests, 147.9 s for 3 questions: 49 s per question, 4.9 s per pair | 15.5 s |
| tev1 mode B (N = 10)  | 2 requests, 76.1 s for 2 questions: 38 s per question | 12.6 s |

tev1 is about 300 times slower than MiniLM per pair on this machine. Mode B
needs one request instead of ten, and each request reads all ten passages:
here it took about three quarters of mode A's time. It is not a faster mode
A: it is a different method, with other results (EXE04, position bias).

## Task

Implement `pick_config(rows, budget_s)` in `exe06.py`: among the rows within
the budget, the highest `evidence_recall@1`; on a tie, the highest `nDCG@3`;
then the cheapest. `None` when nothing fits.

```bash
uv run python exercises/exe06-cost/check.py
```

## Run, one step at a time

### 1. The table

```bash
uv run python exercises/exe06-cost/exe06.py
```

Measured on the dev set (the reranker's CPU seconds per question; tev1 at
N = 50 is not run):

| config                  | `evidence_recall@1` | `nDCG@3` | s/question (CPU) |
|-------------------------|---------------------|----------|------------------|
| nomic · N=10 · none     | 0.636               | 0.661    | 0                |
| nomic · N=10 · minilm   | 0.879               | 0.825    | 0.17             |
| nomic · N=20 · minilm   | 0.909               | 0.866    | 0.31             |
| nomic · N=50 · minilm   | 0.939               | 0.896    | 0.73             |
| nomic · N=20 · bge      | 0.879               | 0.857    | 0.79             |
| nomic · N=20 · tev1-a   | 0.939               | 0.871    | 98.6             |
| bm25 · N=10 · none      | 0.697               | 0.743    | 0                |
| bm25 · N=10 · minilm    | 0.970               | 0.890    | 0.17             |
| bm25 · N=20 · minilm    | 0.970               | 0.908    | 0.31             |
| bm25 · N=20 · tev1-a    | 0.970               | 0.904    | 98.6             |

(The full run prints all 22 rows.)

- With `nomic`, MiniLM gains from depth: 0.879 at N = 10, 0.939 at N = 50,
  for 0.73 s per question.
- tev1 at N = 20 matches MiniLM at N = 50 (0.939) and costs about 130 times
  more.
- BM25 + MiniLM reaches 0.970 already at N = 10: on this dev set, the
  cheapest first stage gives the reranker the best candidates. The questions
  name machines and codes, which BM25 matches exactly.

### 2. Change the budget

```bash
uv run python exercises/exe06-cost/exe06.py --budget 0.5
uv run python exercises/exe06-cost/exe06.py --budget 60
```

Measured: `bm25 · N=20 · minilm` at every budget from 0.5 s to 60 s. A larger
budget does not buy a better row here: tev1 at N = 20 (98.6 s) is out of a
60 s budget, and at N = 10 it only ties MiniLM.

### 3. Batching

The note under the table compares MiniLM with batch 1 and batch 8. Batching
changes the time per pair, not the scores: the quality columns do not depend
on it. On this CPU the gain is not stable: batch 8 was faster in two runs
and slower in one (23.7 against 12.9 ms per pair).

The run also saves the MiniLM and bge cost per pair (N = 20) in
`.cache/measurements/`; EXE08 reads its CPU column from there.

If a tev1 row says "quality not cached", the note names the command that
fills the cache (EXE00 with `--reranker tev1-a --eval`).

These are dev-set numbers: they choose the configuration. EXE08 measures the
chosen pipelines once on the holdout.
