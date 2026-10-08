# EXE03 — The cross-encoder

**Concept:** two ways to score a passage for a question.

```text
bi-encoder (unit 03, the first stage)
  question -> vector        passage -> vector        cosine(vector, vector)
  The two texts never meet. Passage vectors are computed once and cached.

cross-encoder (the reranker)
  (question, passage) -> one token sequence -> one forward pass -> relevance score
  The model reads both texts at once. One pass per pair: too slow for 600
  chunks, fine for 20 candidates.
```

The dedicated reranker of this unit is `Xenova/ms-marco-MiniLM-L-6-v2`, an
ONNX export of a cross-encoder trained to rank passages for search queries.
It runs in the Python process with ONNX Runtime, not in Ollama.

## A relevance score is not a probability

The model returns one number per pair: a **logit**, from about -11 to +10 on
this corpus. A sigmoid maps it into (0, 1), but that is not a calibrated
probability that the passage is relevant: it is the same number on another
scale, for the same reasons as the cosine of unit 03. And the scale belongs
to the model: `bge-reranker-base` gives other numbers for the same pairs.

## Task

Implement `score_pair(tokenizer, session, question, passage)` in `exe03.py`:
encode the pair, build the int64 inputs the model has, run the session,
return the logit as a float, without a sigmoid.

```bash
uv run python exercises/exe03-cross-encoder/check.py
```

## Run, one step at a time

### 1. What the model reads

```bash
uv run python exercises/exe03-cross-encoder/exe03.py --inspect
```

Measured: the pair becomes one sequence, `[CLS] what is p ##n - x ##1 ##q -
199 - a ? [SEP] ke ##strel l ##x - 69 — spare parts p ##n - x ##1 ##q - 199 -
a : second mirror . [SEP]`. The `type_ids` are 0 for the question and 1 for
the passage. Note how the part number is cut into pieces (`p ##n - x ##1 ##q
- 199 - a`): the model sees sub-words, not the identifier. The header line
shows the pinned revision, the file, `max_length` 512 and the load time
(0.19 s).

### 2. Cosine against relevance score

```bash
uv run python exercises/exe03-cross-encoder/exe03.py --case 4
```

"What does E-4210 mean on the Kestrel LX-69?" The table lists the first
stage's cosine, the cross-encoder's logit, its sigmoid, and the gain.

Measured: the cosines of the top candidates are all between 0.68 and 0.72;
the first-stage rank 1 was `laser1-overview-1` (0.717), with gain 0. The
logits spread from 6.59 (the evidence, moved from 6 to 1) to 2.43 (the
overview, moved from 1 to 8). The sigmoids of the first seven rows are all
between 0.97 and 0.999: read as "probabilities", they would say that seven
chunks are almost surely relevant. Only one is.

### 3. The dev set, and how the scores spread

```bash
uv run python exercises/exe03-cross-encoder/exe03.py --eval
```

Measured (`nomic-embed-text`, N = 20): `evidence_recall@1` 0.636 → 0.909,
`nDCG@3` 0.661 → 0.866, the same as EXE00.

The count table shows the logits of every candidate, split into evidence
chunks and irrelevant chunks. Measured: the evidence chunks sit mostly above
3.8 (31 of 36), but 66 irrelevant chunks also score between 5.8 and 7.9, and
4 evidence chunks score below 1.7. The groups overlap: a fixed threshold on
the logit would not separate them, like the cosine in unit 03 EXE05. The
reranker is good at **ordering** the candidates of one question; its scores
across questions are not comparable on a fixed scale.

### 4. Another cross-encoder, another scale

```bash
uv run python exercises/exe03-cross-encoder/exe03.py --eval --reranker bge
```

Measured: `bge-reranker-base` (int8) loads in 1.48 s and gives
`evidence_recall@1` 0.879, `evidence_recall@3` 0.970 and `nDCG@3` 0.857:
slightly worse than MiniLM at rank 1, slightly better at rank 3. Its logits
are on another scale. EXE06 measures what each one costs.
