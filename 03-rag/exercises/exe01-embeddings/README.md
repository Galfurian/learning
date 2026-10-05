# EXE01 — Texts become vectors

**Concept:** an embedding model turns any text into a vector of fixed size:
768 numbers for `embeddinggemma`, whatever the length of the text. Texts
with a similar meaning get vectors that point in similar directions. The
model reads one text at a time and never compares two texts: the APP
computes the similarity.

## Before you start

```bash
uv run python exercises/exe01-embeddings/exe01.py --inspect
```

The yellow TODO panel says that `normalize()` is missing. `--inspect` does
not call the embedding model.

## Task

1. Implement `normalize(vector)` in `exe01.py`: divide the vector by its
   length (L2 norm). A zero vector stays zero. Do not modify the input.
2. Add two pairs to `PAIRS`: one where you expect the FakeEmbedder to fail,
   and one where you expect the real model to fail.

```bash
uv run python exercises/exe01-embeddings/check.py
```

## Run

```bash
uv run python exercises/exe01-embeddings/exe01.py
uv run python exercises/exe01-embeddings/exe01.py --no-prefix
ollama stop embeddinggemma
uv run python exercises/exe01-embeddings/exe01.py --embed-model nomic-embed-text
ollama stop nomic-embed-text
```

The first part uses the FakeEmbedder: it hashes every word (stopwords
removed) into one of 1024 slots and counts. The second part sends every
sentence to the real model and prints a table of pairs.

## What to observe

Measured with the reference solution (`embeddinggemma`, prefixes on):

| pair                                                   | label     | fake  | real  |
|--------------------------------------------------------|-----------|-------|-------|
| The belt squeals at start-up. / … high-pitched noise … | same      | 0.236 | 0.717 |
| Keep the coolant between 15 and 22 °C. / The chiller water must stay cool. | same | 0.000 | 0.633 |
| Never cut PVC on the laser. / PVC must not be cut …    | same      | 0.750 | 0.940 |
| The nozzle is clogged. / The nozzle is clean.          | different | 0.500 | 0.852 |
| Press START twice within 3 s. / Press START once, then wait 3 s. | different | 0.667 | 0.916 |
| Clean the lens every week. / Grease the rails …        | different | 0.224 | 0.568 |

- **The FakeEmbedder sees words, not meaning.** "coolant" and "chiller water"
  share no word, so the fake cosine is 0.000. The real model gives 0.633.
- **The real model is not a meaning detector either.** "The nozzle is
  clogged" and "The nozzle is clean" have opposite meanings and score
  0.852, higher than the "same" coolant pair (0.633). "Press START twice"
  and "Press START once" score 0.916. Most of their words are shared, and
  one word flips the meaning. An embedding measures how close two texts
  are, in a sense the model learned. Whether that closeness is the
  closeness you need is something you measure on your own data (EXE04).
- **Every real vector has norm 1.0000**, for `embeddinggemma` and for
  `nomic-embed-text`. So in the table, "real cosine" and "real dot" are the
  same number.

**Know what your embedding endpoint returns.** Ollama `/api/embed` already
returns unit-length vectors, so the APP does not normalize them again; the
index of EXE04 only checks that the norm is 1. The FakeEmbedder vectors are
raw counts (the first one has norm 1.7321), so for them the APP must
normalize. The lesson is not "always normalize". It is "check".

## Prefixes

`embeddinggemma` documents two input formats: `task: search result | query:
...` for questions, and `title: ... | text: ...` for documents. The unit uses
them by default (here both sentences of a pair are embedded as documents).
`--no-prefix` sends the raw text: the scores move by a few hundredths in
both directions (for example 0.633 -> 0.583, 0.852 -> 0.767).

Follow the model's documented usage, but verify its effect on your
retrieval task. EXE04 measures it on the eval set, where it matters.
