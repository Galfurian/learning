# EXE06 — Token replay

**Concept:** play the trace on the net. When a transition is not enabled,
add the **missing** tokens; at the end, count the **remaining** ones.
Fitness = 0.5 (1 − missing/consumed) + 0.5 (1 − remaining/produced). The
rules are those of pm4py: an activity with no transition (`unmapped:*`) is
skipped with no penalty.

A running order is not a deviation. Replay it with `complete=False`: there
is no final consumption, so the unfinished end costs nothing.

## Task

Implement `token_replay(net, trace, complete=True)`.

```bash
uv run python exercises/exe06-token-replay/check.py
uv run python exercises/exe06-token-replay/exe06.py
```

## What to look at

Measured on the gadget net:

| log | replayed as | fitness | missing | remaining | problems at |
|-----|-------------|---------|---------|-----------|-------------|
| ref-order | running | 1.000 | 0 | 0 | - |
| ref-order | complete | 0.923 | 1 | 1 | - |
| ref-skip-check | running | 0.950 | 1 | 0 | assemble_gadget |
| ref-no-end | running | 1.000 | 0 | 0 | - |
| ref-stuck | complete | 0.923 | 1 | 1 | - |

- `ref-order` as complete looks like a deviation; as running it fits.
  Running is not a deviation.
- `ref-stuck` and `ref-order` give the same replay. Token replay sees the
  order of the operations, not their time. Only the timing (EXE08) tells a
  stuck operation from a running one.
- The skipped check shows at `assemble_gadget`, the first operation that
  needs that token. Replay finds the symptom, not the skipped step. EXE07
  finds the step.

On `train`, per injected deviation, on the true recipe of each order:
174 orders with no deviation, 0 flagged; skip 6 of 6, swap 6 of 6, extra 3
of 3, stuck 3 of 3 flagged. **Gap 0 of 3 and duplicate 0 of 5:** the
abstraction absorbs a lost or a copied low-level event (EXE02), so the
operation sequence is clean and conformance cannot see them. They are
data-quality problems, not control-flow deviations. Find them at the
event level (a mission with no end, two equal events).
