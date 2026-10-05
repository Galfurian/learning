# EXE04 — The index and the eval set

**Concept:** the index is a matrix with one unit vector per chunk. Search is
one matrix-vector product. Measure retrieval on labeled questions before you
generate any answer: if the right section is not retrieved, no prompt can
fix the answer.

## Task

Implement in `exe04.py`:

- `search(vectors, chunks, query, k)`: one matrix-vector product, then the k
  best `Hit`s, rank from 1;
- `recall_at_k(questions, results, k)`: the fraction of answerable questions
  with a chunk of a relevant section in the first k hits.

```bash
uv run python exercises/exe04-retrieval/check.py
```

`exe04.py --eval` prints your recall next to the library's. They must be
equal.

## The cache

Embedding the 43 dev chunks takes about 6 s on CPU. The APP stores every
document vector in `.cache/embeddings/<model>/`, one `.npy` file per text.
Run the eval twice:

```bash
uv run python exercises/exe04-retrieval/exe04.py --eval
uv run python exercises/exe04-retrieval/exe04.py --eval
```

The note line says how many vectors came from the cache, and how many
requests went to the model. On the second run it is "43 vectors from the
cache, 0 request(s)". The cache key is the model name plus the exact text
sent, prefix included. A change of model, prefix or text re-embeds only what
changed, and never reuses a stale vector.

Questions are not cached: each one is one short request, and `--verbose`
always shows it.

## Run and compare

```bash
uv run python exercises/exe04-retrieval/exe04.py --case 8
uv run python exercises/exe04-retrieval/exe04.py --eval
uv run python exercises/exe04-retrieval/exe04.py --eval --no-prefix
uv run python exercises/exe04-retrieval/exe04.py --eval --fake-embed
ollama stop embeddinggemma
uv run python exercises/exe04-retrieval/exe04.py --eval --embed-model nomic-embed-text
ollama stop nomic-embed-text
```

## What to observe

Measured on the 22 answerable dev questions (chunk size 60):

| embedder                         | R@1   | R@3   | R@5   | MRR   | E@3   | misses at k = 3 |
|----------------------------------|-------|-------|-------|-------|-------|-----------------|
| `embeddinggemma`                 | 0.955 | 1.000 | 1.000 | 0.977 | 1.000 | none            |
| `embeddinggemma`, `--no-prefix`  | 0.909 | 1.000 | 1.000 | 0.955 | 1.000 | none            |
| `nomic-embed-text`               | 0.818 | 0.909 | 0.909 | 0.864 | 0.909 | d09 (rank 6), d16 (not in top 10) |
| FakeEmbedder                     | 0.545 | 0.864 | 0.955 | 0.725 | 0.818 | d07 (4), d11 (not in top 10), d16 (5) |

- **R@1 vs R@3.** With `embeddinggemma` one question misses rank 1 (d08, the
  lead-free profile, behind the leaded one), and none misses rank 3. The
  choice of k is a trade: a larger k finds more, and also puts more noise in
  the context (EXE05).
- **Which categories fail.** The FakeEmbedder fails on synonym, distractor
  and part-number questions. `nomic-embed-text` misses d09 ("plate" vs "build
  sheet") and never finds d16 ("What is part PN-X7Q-919-A?") in its top 10:
  it returns the spare-parts sections of the other three machines.
- **The documented prefixes.** With prefixes, R@1 is 0.955; without, 0.909.
  That is one question out of 22: on a set this small, the difference is
  noise. The prefixes stay on because the model documents them, and this
  measurement does not argue against them.

## Dev set

These 26 questions (22 with an answer, 4 without) are the **dev set**. You
will choose the chunk size, k, a threshold and the prompt on them. EXE09
checks the final system on questions you have not seen. If you tune on the
questions you report, the report measures your tuning, not your system.
