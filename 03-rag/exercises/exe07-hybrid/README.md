# EXE07 — Exact identifiers: two retrievers, one ranking

**Concept:** semantic search matches meaning; keyword search matches exact
tokens. Part numbers like `PN-X7Q-991-A`, `PN-X7Q-919-A` and `PN-X7R-919-A`
differ by one or two characters. That difference is the whole meaning, and
an embedding model is not trained to keep such invented strings apart. For a
keyword retriever, each one is a different token. The reason for hybrid
search is structural, not a weakness of one model.

## Why fuse ranks, not scores

The two retrievers give numbers on different scales: a cosine between about
0.3 and 0.7, a keyword score between about 1 and 10. Adding them would let
the keyword score win every time. Reciprocal rank fusion (RRF) uses only the
ranks: every hit adds `1 / (60 + rank)` to its chunk.

## Task

Implement in `exe07.py`:

- `keyword_search(chunks, weights, query, k)`: the sum of `weights[t]` over
  the distinct query tokens `t` that appear in the chunk (`weights` is the
  inverse document frequency: rare tokens weigh more);
- `fuse(rankings, k=60)`: reciprocal rank fusion.

```bash
uv run python exercises/exe07-hybrid/check.py
```

## Run

```bash
uv run python exercises/exe07-hybrid/exe07.py --case 16
uv run python exercises/exe07-hybrid/exe07.py --eval
uv run python exercises/exe07-hybrid/exe07.py --eval --top-k 1
ollama stop embeddinggemma
uv run python exercises/exe07-hybrid/exe07.py --eval --embed-model nomic-embed-text
ollama stop nomic-embed-text
```

## What to observe

`--case 16` ("What is part PN-X7Q-919-A?") with `embeddinggemma`: the
semantic ranking puts the three spare-parts sections at 0.452, 0.437 and
0.434. The right one is first, but by 0.015. The keyword ranking puts it
first with 3.784, against 2.262 for the next chunk: the token
`pn-x7q-919-a` appears in one chunk only.

R@3 on the 22 answerable dev questions (measured with the reference
solution):

| retriever | `embeddinggemma` R@3 | part-number | synonym | `nomic-embed-text` R@3 | part-number | synonym |
|-----------|----------------------|-------------|---------|------------------------|-------------|---------|
| semantic  | 1.000                | 3/3         | 5/5     | 0.909                  | 2/3         | 4/5     |
| keyword   | 0.773                | 3/3         | 2/5     | 0.773                  | 3/3         | 2/5     |
| fused     | 0.955                | 3/3         | 4/5     | 0.909                  | 2/3         | 4/5     |

- **Keyword search finds every part number**, with either embedder, and
  finds only 2 of the 5 synonym questions: it has no meaning to fall back on.
- **Semantic search with `embeddinggemma` already finds every part number on
  this dev set**, but by a margin of hundredths. `nomic-embed-text` misses
  d16 completely: no spare-parts chunk of the LX-40 in its top 10.
- **Fusion did not fix d16.** RRF rewards chunks that both retrievers rank
  high. A chunk that only the keyword retriever finds gets 1/61 = 0.016; a
  chunk that both put at rank 3 gets 2/63 = 0.032. With `nomic-embed-text`,
  the exact match loses to chunks both retrievers half agree on. On this dev
  set, fusion costs a little where semantic search is already right, and
  does not save the identifier question it was meant for.

This is the honest result on 22 questions with only three part numbers. Two
things change in EXE09: the plant has 40 machines, five of each type, with
look-alike codes and part numbers in every manual. That is where the
structural argument is tested. Other fusions exist: weights per retriever,
or routing a query that contains a known identifier to keyword search
first. The extras try one.

## In the pipeline

```bash
uv run python exercises/exe00-demo/exe00.py --retriever hybrid --case 16
```

This uses the library version (`raglab.hybrid`: BM25 instead of your simple
weights, fused with RRF). The answer is "PN-X7Q-919-A: first mirror, gold
coated. [lx40-parts-1]".
