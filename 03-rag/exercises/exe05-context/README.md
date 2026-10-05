# EXE05 — The context, and when to abstain

**Concept:** the context is all the generator reads. The APP chooses what
goes in (which chunks, in which order, with which ids, within which budget)
and whether to call the generator at all.

## Task 1: build the context

Implement `build_context(hits, budget)` in `exe05.py`: rank order, each chunk
once, each chunk as `format_chunk(chunk)` (`[id]` on the first line), chunks
joined by a blank line. A chunk that does not fit in what is left of the
budget is dropped, and the next one is still tried.

```bash
uv run python exercises/exe05-context/check.py
```

The check fails on `THRESHOLD` until Task 2.

## Run

```bash
uv run python exercises/exe05-context/exe05.py
```

Read the histogram first. It shows the top-1 score of the 26 dev questions,
split into questions the manuals can answer and questions they cannot.

## A score threshold is a policy, not a solution

Measured with `embeddinggemma` on the dev set:

- lowest top-1 score of an answerable question: **0.349** (d18, "What is
  PN-X7S-919-A?");
- highest top-1 score of a no-answer question: **0.558** (d25, "What is the
  maximum engraving resolution of the LX-40 in DPI?" — the LX-40 overview
  is a close match, but it has no DPI);
- the no-answer questions score 0.325, 0.462, 0.531 and 0.558, and 11 of the
  22 answerable questions score less than 0.558.

The two groups **overlap**. No threshold separates them: each threshold
either refuses some answerable questions or lets some no-answer questions
through. The threshold table shows the trade for every threshold: how many
answerable questions it refuses, how many no-answer questions it passes,
and the cost.

The cost is yours to set. `COST_MISS = 5` says a refused answer costs five
times as much as a wrong accept (`COST_FALSE = 1`). With these costs, the
cheapest threshold is any value above 0.325 and up to 0.349: it refuses d24
(the oscilloscope) and keeps every answerable question. Three no-answer
questions still pass. Change the costs, and the cheapest threshold moves.

A threshold holds for one embedding model, with one prefix setting. With
`nomic-embed-text`, the no-answer questions score 0.626–0.724 and the lowest
answerable one 0.531 (EXE04): a value chosen for `embeddinggemma` means
nothing there.

Finally, the dev set has only 4 no-answer questions. Any threshold chosen on
it rests on very little data.

## Task 2: the policy

Set `THRESHOLD` from the table, and implement `answerable(hits)`: true when
the best hit scores at least `THRESHOLD`.

```bash
uv run python exercises/exe05-context/check.py
uv run python exercises/exe05-context/exe05.py
uv run python exercises/exe05-context/exe05.py --case 24
```

## What the threshold still lets through

With `THRESHOLD = 0.33`, d23 (warranty, 0.462), d25 (DPI, 0.558) and d26
(nitrogen flow, 0.531) still reach the generator, with three chunks that do
not contain the answer. The generator's refusal is the second check: EXE06
shows that the generator refused all three.

Other signals use more than the top-1 score: the margin between the first
two hits, a reranker, a keyword match (EXE07). The extras in
`exercises/README.md` try some of them.
