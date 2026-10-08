# EXE08 — The benchmark

This one is solved. It compares three pipelines on the **holdout**: 20
questions written and committed before the first benchmark run, on 8
machines that the dev set does not use.

```text
A  embedding                  -> top 3 -> generator
B  embedding -> tev1 (mode A) -> top 3 -> generator
C  embedding -> MiniLM        -> top 3 -> generator
```

Same first stage (`nomic-embed-text`, N = 20), same k = 3, same generator
(`qwen3:1.7b`). A second set of runs repeats A–C with `embeddinggemma` as the
first stage.

The pipelines follow the spec ("embedding → …"). On the dev set, EXE06
picked BM25 + MiniLM as the best configuration under a CPU budget; that is a
dev-set finding, and it is not applied here.

## Read the columns

- **Retrieval and reranking:** `evidence_recall@1`, `evidence_recall@3`,
  `MRR@3` and `nDCG@3` of the top 3 the generator reads.
- **Answers:** `facts` and `citations ok` are code checks (coarse, as in
  unit 03); `false_answer_rate` and `abstention_accuracy` are on the 3
  no-answer questions.
- **Cost:** reranker requests per question, the reranker's CPU seconds per
  question (the CPU cost per pair measured in EXE06 for MiniLM and bge, and by
  `scripts/measure_tev1_cpu.py` for tev1, times the candidates of each
  question), and the time of this run. This run used the score
  cache, and the tev1 runs used a lab GPU: that column is not a cost.

## Results

Measured (17 answerable questions, 3 without an answer):

| run              | `evidence_recall@1` | `evidence_recall@3` | `MRR@3` | `nDCG@3` | facts | reranker s/question (CPU) |
|------------------|---------------------|---------------------|---------|----------|-------|---------------------------|
| A nomic          | 0.65                | 0.71                | 0.68    | 0.66     | 11/17 | 0                         |
| B nomic + tev1   | 0.94                | 0.94                | 0.94    | 0.89     | 14/17 | 98.6                      |
| C nomic + MiniLM | 0.88                | 0.94                | 0.91    | 0.85     | 14/17 | 0.26                      |
| A gemma          | 0.88                | 0.94                | 0.91    | 0.88     | 16/17 | 0                         |
| B gemma + tev1   | 1.00                | 1.00                | 1.00    | 0.94     | 14/17 | 98.6                      |
| C gemma + MiniLM | 0.88                | 1.00                | 0.94    | 0.89     | 14/17 | 0.26                      |

Citations were valid in 20 of 20 answers in every run, and every pipeline
refused the 3 no-answer questions (`false_answer_rate` 0.00).

**With `nomic` as the first stage**, both rerankers close most of the gap:
`evidence_recall@1` from 0.65 to 0.88 (MiniLM) or 0.94 (tev1), and 3 more
correct answers. tev1 is a little better at rank 1, and about 380 times
slower per question on the CPU. One question (h06, "What is part
PN-X1U-991-A?") stays wrong: its evidence is not among the 20 candidates,
and no reranker can bring it back.

**With `embeddinggemma`**, the first stage is already good. tev1 reaches 1.00
at every retrieval metric, MiniLM 0.88 at rank 1 and 1.00 at rank 3. Yet the
answers got **worse** with both rerankers: 16/17 without a reranker, 14/17
with either. The failing questions show why:

- h08: the reranked top 3 is the right parts list **and** the parts lists of
  two sibling ovens; the generator gave a look-alike number ("PN-X5S-919-A",
  the exhaust damper). Without a reranker, the top 3 held one parts list,
  between the calibration and the settings sections, and the answer was
  right.
- h06: with and without the reranker, the right parts list was first, next
  to two look-alike lists; with MiniLM the generator read the wrong line
  ("PN-X1U-991-A is a tool holder" — the tool holder is PN-X1U-199-B).
- h13: the same chunk was at rank 1 with and without the reranker, and the
  generator answered once and refused once. That is generation noise, not
  the reranker.

On 17 questions, a difference of two answers is within that noise. The
retrieval numbers are the stable result: a reranker improves the order of
the candidates; a correct order is necessary for a correct answer, and not
sufficient.

## Run it yourself

```bash
uv run python exercises/exe08-benchmark/exe08.py --pipeline embedding --eval
uv run python exercises/exe08-benchmark/exe08.py --pipeline minilm --eval
uv run python exercises/exe08-benchmark/exe08.py --pipeline tev1 --eval    # slow on a CPU: about 100 s per question
uv run python exercises/exe08-benchmark/exe08.py --pipeline minilm --eval --first-stage gemma
uv run python exercises/exe08-benchmark/exe08.py --compare
```

`--case N` runs one holdout question and shows the reranked top 3, the
answer and the first failing stage. With `OLLAMA_HOST=host:port` every
Ollama call (embedding, tev1, generator) goes to that machine.
