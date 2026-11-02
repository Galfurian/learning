# EXE02 — Event abstraction

**Concept:** the line does not log "step 4 of the recipe". It logs what a
machine does: a robot mission started and ended, a pallet stayed at a bay, a
check passed. A recipe operation is a pattern of these low-level events.
`load_board` is two robot_a missions; `test_board` is a stay at the tester
bay and a test result. **Abstraction** maps the low-level events to
operations, each with a start and a complete entry.

The recipe of the order is not known yet, so the events are matched against
the operations of all recipes. `reload_covers` has the same missions as
`load_covers`: only the context (a `bin_covers` before it) tells them apart.
Every entry is `inferred`: it is a mapping, not a reading.

## Task

Implement `match_operations(case, units)`: for one order, say which
operation each low-level unit is evidence of. A unit is one robot mission
(started + ended) or one event. pmlab does the rest around your function:
it pairs the missions into units, places the bay stays after you, and
builds the start and complete entries.

Your function decides:

- the operations a unit can be evidence of (`case.candidates`), or none
  (`unmapped`);
- the fail-branch rule: a covers load after `bin_covers` is
  `reload_covers`, before it is `load_covers`;
- whether the unit joins an instance that is already open (a step it lacks,
  a duplicated record, one more part of the assembly) or starts a new one.

```bash
uv run python exercises/exe02-abstraction/check.py
uv run python exercises/exe02-abstraction/exe02.py                  # ref-order
uv run python exercises/exe02-abstraction/exe02.py --log train
```

The reference solution is about 35 lines. The whole module is
`src/pmlab/abstraction.py`.

## What to look at

Measured on `ref-order`: 56 events → 21 entries, 10 operations completed,
every event cited. `engrave_gadget` has a start and no complete: its mill
stay is still open at the end of the log.

On `train`: 5,854 events, 5,848 in an order (the correlation leaves 6 out),
3,027 entries, 1,513 operations completed.

Look at `ref-no-end`: a mission end of `bin_covers` is missing (injected).
The entries are the same as on `ref-order`. The abstraction absorbs the gap:
the operation completes at its last evidence. This is good for the process
view, and it hides a data-quality problem. EXE06 and EXE07 come back to it.
