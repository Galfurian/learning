# EXE08 — Performance

**Concept:** with a start and a complete per operation, the log gives the
**service time** (complete − start) and the **waiting time** (start − the
complete of the step it depends on). Percentiles over many orders make a
**baseline**. An operation that is open for longer than the p95 is
**unusual**. The nominal time of the recipe is shown next to it, not used
alone: the measured baseline is what the line does.

## Task

Implement `performance(traces)`.

```bash
uv run python exercises/exe08-performance/check.py
uv run python exercises/exe08-performance/exe08.py
```

## What to look at

Measured on `train` (selected rows, seconds):

| operation | n | p50 | p95 | max | wait p50 | wait p95 | nominal |
|-----------|---|-----|-----|-----|----------|----------|---------|
| reserve_pallet | 200 | 51 | 83 | 110.6 | - | - | 10 |
| check_covers | 120 | 10.7 | 91.8 | 115.3 | 8.4 | 424.8 | 10 |
| engrave_gadget | 100 | 148.2 | 216.5 | 269.6 | 18.7 | 39.6 | 150 |
| build_bricks | 35 | 117.5 | 161.5 | 162.7 | 18.3 | 598.4 | 120 |

- `reserve_pallet` takes 51 s at p50 against a nominal 10 s: the evidence
  is a bay stay, and the stay holds the time the pallet waits for its
  load. Nominal and measured are not the same thing.
- The longest wait (p95) is before `build_bricks`, 598.4 s: orders share
  the assembly cell. That is the bottleneck.
- `check_covers` waits 424.8 s at p95: after a failed check, the next
  check waits for the reload.

Open operations with these baselines:

| log | now | operation | age | p95 | verdict |
|-----|-----|-----------|-----|-----|---------|
| ref-order | 1118 | engrave_gadget | 200 | 216.5 | running |
| ref-stuck | 1400 | engrave_gadget | 482 | 216.5 | unusual |

"Unusual" is a comparison with a baseline, not a cause. The log does not
say why the engrave is slow.
