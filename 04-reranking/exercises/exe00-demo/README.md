# EXE00 — First stage, reranker, generator

Nothing to write. Read the file, run it, and compare the stages.

```text
QUESTION -> FIRST STAGE   nomic-embed-text, scores all 600 chunks alone   -> 20 candidates
         -> RERANKER      MiniLM cross-encoder, reads question + candidate -> new order, top 3
         -> GENERATOR     qwen3:1.7b reads the top 3                      -> answer
```

Four actors: the APP (the exercise file and `src/reranklab`), the EMBEDDING
MODEL, the RERANKER and the GENERATIVE MODEL.

**A reranker can only reorder the candidates the retriever already found.**
If the right chunk is not among the 20, no reranker brings it back.

## Why `nomic-embed-text` as the first stage

Unit 03 used `embeddinggemma`, the stronger embedder. Here the first stage is
`nomic-embed-text` on purpose, because the measurements show a gap a reranker
can close. On the 33 answerable dev questions:

| first stage        | `evidence_recall@1` | `section_recall@3` | `nDCG@3` |
|--------------------|---------------------|--------------------|----------|
| `nomic-embed-text` | 0.636               | 0.758              | 0.661    |
| `embeddinggemma`   | 0.939               | 1.000              | 0.911    |

With `embeddinggemma` there is little left to rerank. Step 3 shows it.

## Without a model

```bash
uv run python exercises/exe00-demo/check.py
uv run python exercises/exe00-demo/exe00.py --inspect
```

The check reranks two fake candidates with the FakeReranker. `--inspect`
prints the setup line (Ollama address, first stage, depth, reranker, top k)
and calls no model.

## Run, one step at a time

### 1. The reranker moves a chunk from rank 20 to rank 1

```bash
uv run python exercises/exe00-demo/exe00.py --case 2 --reranker none
uv run python exercises/exe00-demo/exe00.py --case 2
```

"On the Tamarin C-83, what is E-5310?" Look at the "gain" column of the
first-stage table: the evidence chunk (gain 2) is not in the first 10. Then
look at the "from" column of the reranked table.

Measured: `conveyor4-errors-2` moved from rank 20 to rank 1 (relevance score
7.05), and the answer is "E-5310: sensor S42 does not respond". The evidence
was the last of the 20 candidates: with a depth of 19, the reranker would
never have seen it.

### 2. The whole dev set

```bash
uv run python exercises/exe00-demo/exe00.py --eval
```

`--eval` does not call the generator: it compares the first stage's order
with the reranked order.

Measured:

| `nomic-embed-text`, N = 20 | `section_recall@3` | `evidence_recall@1` | `evidence_recall@3` | MRR   | `nDCG@3` |
|----------------------------|--------------------|---------------------|---------------------|-------|----------|
| first stage                | 0.758              | 0.636               | 0.727               | 0.713 | 0.661    |
| + MiniLM                   | 0.939              | 0.909               | 0.939               | 0.930 | 0.866    |

Two questions stay wrong. Case 7 ("What is part PN-X1Q-199-A?"): the evidence
is not among the 20 candidates, so nothing can fix it here. Case 28 (a
paraphrase): the evidence is at rank 5 before and after.

### 3. A strong first stage leaves little to rerank

```bash
uv run python exercises/exe00-demo/exe00.py --eval --first-stage gemma
```

Measured:

| `embeddinggemma`, N = 20 | `section_recall@3` | `evidence_recall@1` | `evidence_recall@3` | MRR   | `nDCG@3` |
|--------------------------|--------------------|---------------------|---------------------|-------|----------|
| first stage              | 1.000              | 0.939               | 1.000               | 0.965 | 0.911    |
| + MiniLM                 | 0.970              | 0.970               | 0.970               | 0.973 | 0.908    |

The reranker fixes two questions and breaks one: case 28 drops from rank 1 to
rank 8. With a first stage this good, the reranker costs time and gains
almost nothing; on this dev set its nDCG@3 is slightly lower.

### 4. The four actors

```bash
uv run python exercises/exe00-demo/exe00.py --verbose --case 2
```

You see `APP -> EMBEDDING MODEL` (the question) and `APP -> GENERATIVE MODEL`
(the top 3 and the question). There is no HTTP call for the RERANKER: MiniLM
runs inside the Python process, with ONNX Runtime. EXE04 uses a reranker that
does call Ollama (`tev1`).

### 5. A question the manuals cannot answer

```bash
uv run python exercises/exe00-demo/exe00.py --case 37
```

"What does error E-4999 mean on the Kestrel LX-69?" Look at the gain column:
every candidate has gain 0. The reranker still produces a top 3 (the LX-69
error codes, scores 5.55, 5.10, 4.67): it orders whatever it gets, relevant
or not.

Measured: the generator replied "Not in the manuals", and the summary line
says "no-answer question: refused". The refusal came from the generator, not
from the reranker.
