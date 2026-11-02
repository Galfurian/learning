# EXE04 — The Alpha miner

**Concept:** discovery builds a Petri net from the log alone. The Alpha
algorithm reads the footprint (`->` causality, `||` parallel, `#` choice)
and makes one place per maximal pair of activity sets. It assumes a
complete log with no noise. The runner also shows the **inductive miner**
of pm4py (not written by hand here): it always gives a sound model that
replays the log.

## Task

Implement `alpha(traces)`.

```bash
uv run python exercises/exe04-alpha/check.py
uv run python exercises/exe04-alpha/exe04.py
```

## What to look at

Measured on `train`, token replay of each net on the traces it comes from
(`fit` = traces with fitness 1.0):

| orders | variants | n | alpha fitness | alpha fit | IM fitness | IM fit |
|--------|----------|---|---------------|-----------|------------|--------|
| brick_demo | all | 36 | 0.931 | 0 | 1.000 | 36 |
| brick_demo | >= 3 | 33 | 1.000 | 33 | 1.000 | 33 |
| parts_test | all | 61 | 0.937 | 0 | 1.000 | 61 |
| parts_test | >= 3 | 55 | 1.000 | 55 | 1.000 | 55 |
| gadget, no fail | all | 83 | 0.927 | 0 | 1.000 | 83 |
| gadget, no fail | >= 3 | 77 | 0.864 | 0 | 1.000 | 77 |
| gadget, fail | all | 17 | 0.837 | 0 | 1.000 | 17 |
| gadget, fail | >= 3 | 14 | 1.000 | 14 | 1.000 | 14 |
| all orders | all | 200 | 0.872 | 0 | 1.000 | 200 |
| all orders | >= 3 | 179 | 0.889 | 0 | 1.000 | 179 |

- **Noise breaks Alpha.** Three injected brick_demo orders (a swap, a skip,
  a stuck order) make `build_bricks` and `check_bricks` look parallel and
  add `check_bricks` as an end. No trace fits. With the frequent variants only, the net fits all 33.
- **Incompleteness breaks Alpha.** "gadget, no fail" does not fit even
  with the frequent variants: the log does not show every order of the
  parallel loads, so the footprint is wrong.
- **The fail branch is a loop of length 3** (`check_covers`, `bin_covers`,
  `reload_covers`, then `check_covers` again). Alpha handles it on clean
  data; it cannot handle loops of length 1 or 2 (see the check).
- **The inductive miner fits everything** and pays in precision: its tree
  for "gadget, fail" has `X( tau, 'test_board' )`, so it allows an order
  with no board test. Fitness alone does not say a model is good.
- **Several recipes in one log** ("all orders"): no single Alpha net fits.
  The recipes are the better model (EXE05).
