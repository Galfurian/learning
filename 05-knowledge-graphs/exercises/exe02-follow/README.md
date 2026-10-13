# EXE02 — Follow a relation path

**Concept:** a graph query is a path of relations. "Which mission is
confirmed by the first rover's status result?" is

```text
rover1 -contains-> rover1/Status -exposes_variable-> rover1/Status/LastResult -confirms-> mission
```

No model reads the graph: a loop over relations and a dict lookup per hop.
A relation written `^name` walks the edge backwards ("which devices serve
bay 5?" is `bay:5 -^serves_bay->`).

## Task

Implement `follow(graph, start, relations)` in `exe02.py`.

```bash
uv run python exercises/exe02-follow/check.py
```

## Run

```bash
uv run python exercises/exe02-follow/exe02.py
```

Every dev question with a gold path runs twice: on the tree only (EXE01)
and on the gold graph. ✓ means the gold answer set came back; a number is
how many nodes came back instead.

Measured: tree only **6/35**, gold graph **35/35**.

- The 6 that the tree answers use tree relations only (`returns`,
  `has_parameter`, `^exposes_variable`, `contains`, `^has_alarm`).
- d12, d13, d16 start in the tree (`contains -> exposes_variable`) and end
  on a link (`confirms`): the tree takes them halfway and stops.
- Every question about bays, items, alarms that stop devices, or incidents
  returns 0 nodes on the tree.

The gold graph is the ceiling: a perfect extraction. EXE03 and EXE04
measure how far a real one gets.
