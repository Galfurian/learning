# EXE03 — The directly-follows graph

**Concept:** the simplest process model is a graph of "b comes directly
after a", with a count and a time on each edge. A **variant** is one
distinct sequence of activities. Rare edges are often noise or deviations;
a filter on the count hides them.

## Task

Implement `dfg(traces)`.

```bash
uv run python exercises/exe03-dfg/check.py
uv run python exercises/exe03-dfg/exe03.py
uv run python exercises/exe03-dfg/exe03.py --min-count 10
```

## What to look at

Measured on `train`: 49 edges, 30 seen 3 times or more, 19 rare ones (26
pairs). Every trace starts with `reserve_pallet`. 32 variants over 200
traces; the five most frequent cover 144 traces.

- `check_covers -> load_board` (38 times) is not a step of any recipe.
  `load_board` and `load_covers` run at the same time on different pallets,
  so the log shows them in either order. A DFG shows concurrency as edges
  in both directions.
- The median gap on `assemble_gadget -> engrave_gadget` is 171.2 s: the
  complete of the first to the complete of the next. It is not a waiting
  time (EXE08).
- One trace ends with `load_board`: a stuck order (injected).
