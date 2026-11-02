# EXE01 — The event log and the case notion

**Concept:** an event log is a list of cases. Each case is a list of events
with an activity and a time. The **case notion** is your choice: what is one
case? On this line, one order uses three pallets and two robots. If the case
is the order, the log keeps every entry once. If the case is the pallet:

- an entry with no pallet (a robot mission, `bin_covers`) is in no case: it
  is **lost**;
- an entry with two pallets (`assemble_gadget` joins the board pallet and
  the covers pallet) is in two cases: it is **copied**;
- the line reuses pallet ids, so one pallet case holds parts of many orders.

## Task

Implement `to_log(entries, case_notion)`.

```bash
uv run python exercises/exe01-event-log/check.py
uv run python exercises/exe01-event-log/exe01.py                    # train
uv run python exercises/exe01-event-log/exe01.py --log ref-order
```

## What to look at

Measured on `train`: 3,027 entries. By order: 200 traces, 3,027 entries. By
pallet: 10 traces, 2,794 entries. 759 entries have no pallet (lost), 526
have two or more (copied).

On `ref-order` the order is one trace of ten operations. Its three pallets
see three short traces: pallet 7 has `reserve_pallet > load_covers >
check_covers`, and none of them has `bin_covers`. Which case notion lets
you ask "which recipe does this order follow"?
