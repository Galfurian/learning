# EXE10 — The object-centric log

**Concept:** an event can touch several objects: an order, one or two
pallets, a robot. An **object-centric event log** (OCEL) keeps all of them.
A flat log chooses one object type as the case, and that choice makes two
errors:

- **convergence:** one event is copied into several cases (the assembly
  joins two pallets, so it is in both pallet cases);
- **divergence:** one case holds several instances of an activity that
  belong to different other objects (a reused pallet loads a board for two
  orders; one order checks covers on two pallets).

## Task

Implement `ocel(entries)` and `flattening_errors(o, object_type)`.

```bash
uv run python exercises/exe10-ocel/check.py
uv run python exercises/exe10-ocel/exe10.py
```

## What to look at

Measured on `train`: 3,027 events; 200 orders, 10 pallets, 7 resources.

| case type | cases | events in cases | convergence | divergence |
|-----------|-------|-----------------|-------------|------------|
| order | 200 | 3027 | 0 | 19 |
| pallet | 10 | 2794 | 526 | 125 |

The order case has divergence 19 and that is correct: after a failed check
the covers come back on a new pallet, so one order holds two
`check_covers` (and `reload_covers`) on different pallets. The pallet case
copies 526 events and mixes orders. The order is the right case for "which
recipe, where is it, did it conform". The pallet is the right case for
"where is this pallet now". An OCEL keeps both questions open.
