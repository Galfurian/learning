# EXE07 — Alignments

**Concept:** an alignment is the cheapest way to explain a trace with a run
of the net. A **sync** move is a trace entry the net can do. A **log** move
is an entry the net cannot do here: "extra". A **model** move is a step the
net needs and the trace does not have: "skipped". Log and model moves cost
1, sync and silent moves 0. Each move keeps its event ids, so a deviation
is a cited fact.

An activity with no transition (`unmapped:*`) is always a log move here.
Token replay ignores it. The evidence lines of EXE00 leave unmapped
activities out of the moves and give them a coverage line.

## Task

Implement `align(net, trace, complete=True)`.

```bash
uv run python exercises/exe07-alignments/check.py
uv run python exercises/exe07-alignments/exe07.py
```

## What to look at

Measured on the gadget net:

| log | aligned as | cost | non-sync moves |
|-----|------------|------|----------------|
| ref-order | running | 0 | - |
| ref-skip-check | running | 1 | model check_covers |
| ref-no-end | running | 0 | - |
| ref-stuck | complete | 2 | model engrave_gadget; model deliver_gadget |

- `ref-skip-check`: the alignment names the skipped step (`check_covers`
  after `reload_covers`). Token replay (EXE06) found only the symptom.
- The fail branch is in the net: the first failed `check_covers`,
  `bin_covers` and `reload_covers` are sync moves. A failed check is not a
  deviation.
- `ref-stuck` as complete: the open `engrave_gadget` and the missing
  delivery are model moves. As running they cost 0. The alignment cannot
  tell "stuck" from "not yet"; the time can (EXE08).

On `train`, per injected deviation: no deviation 0 of 174 with cost > 0;
skip 6 of 6, swap 6 of 6, extra 3 of 3, stuck 3 of 3; gap 0 of 3 and
duplicate 0 of 5 (absorbed by the abstraction, as in EXE06).
