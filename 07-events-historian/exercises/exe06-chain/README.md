# EXE06 — The evidence chain of one case

**Concept:** a chain is one case in time order, with each assignment checked
against the movements: a pallet *was at* a bay only if it left the loop
while assigned. The segment events are evidence, not steps.

## Task

Implement `chain(events, case_id)`.

```bash
uv run python exercises/exe06-chain/check.py
uv run python exercises/exe06-chain/exe06.py
```

## What to look at

The story of `p7#1`: two stays (load/unload bay 284–371 s, QC bay 392–523
s), the QC check (inferred), robot_b's rework missions (inferred), the
coverage line. Each line keeps the ids of the events it summarizes, so a
citation still points at evidence.
