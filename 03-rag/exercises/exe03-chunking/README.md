# EXE03 — Chunking

**Concept:** the unit of retrieval is the chunk, not the document. Each chunk
gets one vector, and the context holds whole chunks.

- Too small: a chunk loses the words that give it meaning. "Check the
  tension." — of what?
- Too big: one vector averages many topics, and the context fills up with
  text the question does not need.

## Task

Implement `chunk_section(section, size, overlap)` in `exe03.py`: windows of
`size` words, each one starting `size - overlap` words after the previous
one, with the line `"<manual> — <section title>"` on top when `WITH_TITLE`
is true. The comment in the file lists every rule.

```bash
uv run python exercises/exe03-chunking/check.py
```

Later exercises use `raglab.chunking.chunk_section`. When you are done,
compare yours with it.

## Run

```bash
uv run python exercises/exe03-chunking/exe03.py --inspect --size 15 --overlap 3
uv run python exercises/exe03-chunking/exe03.py
uv run python exercises/exe03-chunking/exe03.py --fake-embed
```

With `--size 15`, the `lx40-errors` section becomes 7 chunks, and windows cut
between a code and its meaning: `lx40-errors-2` starts with "once. Close the
lid, check the reed switch…" — the code E-4021 is in the chunk before. The
title line still says which manual and which section the words come from.

The full run chunks all four manuals with your function at sizes 15, 30, 60,
120 and 400 words, plus one row with the library chunker without the title
line, and measures each on the 26 dev questions.

## What to observe

Measured with the reference solution (overlap = min(15, size / 4)):

| chunker              | chunks | `embeddinggemma` R@1 / E@1 / E@3 | FakeEmbedder R@1 / E@1 / E@3 |
|----------------------|--------|----------------------------------|------------------------------|
| size 15              | 119    | 0.909 / 0.727 / 1.000            | 0.591 / 0.318 / 0.682        |
| size 30              | 64     | 0.955 / 0.955 / 1.000            | 0.500 / 0.455 / 0.818        |
| size 60 (default)    | 43     | 0.955 / 0.955 / 1.000            | 0.545 / 0.545 / 0.818        |
| size 120             | 35     | 0.955 / 0.955 / 1.000            | 0.682 / 0.682 / 0.909        |
| size 60, no title    | 43     | 0.909 / 0.864 / 1.000            | 0.500 / 0.500 / 0.727        |

- **Size 15 is too small.** The right section is still found (R@1 0.909),
  but the first chunk often does not hold the fact (E@1 0.727): the answer is
  in the next window.
- **The title line matters.** Every manual has a "Maintenance schedule", an
  "Error codes" and a "Spare parts" section. Without the title, "grease the
  roller bearings every 500 hours" does not say it is the conveyor. E@1 drops
  from 0.955 to 0.864. Set `WITH_TITLE = False` in your file and run again.
- **At k = 3 the strong model hides all of this.** With `embeddinggemma`,
  E@3 is 1.000 for every row: the dev manuals are short, and three chunks
  almost always include the right one. The FakeEmbedder, which has no
  meaning to fall back on, shows the effect at k = 3 too.

This is a property of this dev set, not a rule: the plant manuals of EXE09
are longer, and there the chunk size is a real choice.

## Two metrics

- **R@k** (by section) is lenient: any chunk of a relevant section counts.
- **E@k** (by evidence) asks whether the top k chunks contain the facts a
  correct answer needs (the `must_contain` strings of each question).

Chunking changes E@k more than R@k. R@k can say "found" when the chunk that
was found holds the wrong half of the section.
