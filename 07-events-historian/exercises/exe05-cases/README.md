# EXE05 — Product cases and inferred links

**Concept:** pallet ids repeat: a pallet comes back for the next product. A
case is a pallet plus a product cycle (`p7#1`); a cycle starts when the
pallet is assigned to the load/unload bay. Most signals do not name a
pallet: the QC check and the robot that reworks a pallet are attached to it
by **inference**, from the time the pallet occupied the QC bay.

## Task

Implement `assign_cases(events)`.

```bash
uv run python exercises/exe05-cases/check.py
uv run python exercises/exe05-cases/exe05.py
```

## What to look at

Measured: 1,323 events, 227 in a case, 18 inferred links. Every inferred
event carries a `confidence_note` with the rule, the version and the
interval it used. Two pallets at the QC bay at once, or no pallet there: no
case, and the answer must abstain.
