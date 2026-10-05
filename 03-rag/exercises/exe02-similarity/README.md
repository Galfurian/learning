# EXE02 — Rank chunks by similarity

**Concept:** retrieval is ranking. Score every chunk against the question
vector, and keep the best k. For unit vectors the cosine is the dot product,
so the index of EXE04 does all of it with one matrix product.

## Task

Implement in `exe02.py`:

- `cosine(a, b)`: `dot(a, b) / (|a| * |b|)`, and 0.0 when one vector is zero;
- `top_k(query, vectors, ids, k)`: the k best `(id, score)` pairs, best first,
  equal scores in their original order.

```bash
uv run python exercises/exe02-similarity/check.py
```

## Run

```bash
uv run python exercises/exe02-similarity/exe02.py --case 9
uv run python exercises/exe02-similarity/exe02.py --eval
```

`--case 9` ranks the 43 dev chunks for "My prints don't stay attached to the
plate." with your `top_k()` and shows the text of the best three.
`--eval` runs the 26 dev questions twice, with the FakeEmbedder and with
`embeddinggemma`, and shows the rank of the first chunk from a relevant
section.

## What to observe

Measured with the reference solution:

| embedder              | R@1  | R@3  |
|-----------------------|------|------|
| FakeEmbedder          | 0.55 | 0.86 |
| `embeddinggemma`      | 0.95 | 1.00 |

- **Where the word count fails.** d11 "Tiny resistors lift up vertically
  after soldering" (the manual says "small components stand up on one
  end"): not in the fake top 10; rank 1 for the real model. d07 "How hot can
  the printer nozzle go before it is damaged?": fake rank 4, real rank 1.
- **Where it holds.** Questions that repeat the manual's words: d01 "vinyl",
  d10 "clicking", d17 "0.6 mm nozzle" are rank 1 for both.
- **Part numbers.** d16 "What is part PN-X7Q-919-A?": fake rank 5, real
  rank 1. Exact identifiers come back in EXE07.
- **The real model is not perfect.** d08 (lead-free peak) is rank 2 for
  both embedders: the leaded profile ranks first.

## A score is not a probability

Look at the top-1 score columns. The same question gets very different
numbers from the two embedders: d09 gets 0.079 (fake) and 0.419 (real), d19
gets 0.379 and 0.737. Even with one embedder, a correct top-1 can score
0.349 (d18) while the top-1 of a question with no answer scores 0.558 (d25).

A cosine of 0.6 does not mean "60% relevant". It is a geometric quantity.
Its scale depends on the model, the prefixes and the length of the texts. A
threshold on it is a choice your app makes, for one model. EXE05 shows how
to choose it, and why it can fail.
