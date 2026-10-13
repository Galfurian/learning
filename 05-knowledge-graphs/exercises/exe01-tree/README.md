# EXE01 — The data model as a tree

**Concept:** a data model is already a graph. Every device file holds
folders, variables, methods and alarm flags; a parser turns them into nodes
and typed edges, with no model and no errors. The same parser also shows
what the data model does **not** hold: any edge between two devices.

## Task

Implement `parse_model(data, file, graph)` in `exe01.py`. The TODO lists the
node ids, the types, the six tree relations, the sources and the props.

```bash
uv run python exercises/exe01-tree/check.py
```

## Run, one step at a time

### 1. One device

```bash
uv run python exercises/exe01-tree/exe01.py --device rover1
```

The table lists the edges of one device: `contains` for the folders,
`exposes_variable` and `exposes_method` inside them, `has_parameter` and
`returns` under each method, `has_alarm` for each flag in `Alarms`. Every
edge has its source: the file and the path inside the device.

### 2. The whole line

The same run ends with the counts per relation, yours against the
reference. Measured with the reference solution:

| relation           | edges |
|--------------------|-------|
| `contains`         | 62    |
| `exposes_method`   | 43    |
| `exposes_variable` | 118   |
| `has_alarm`        | 32    |
| `has_parameter`    | 21    |
| `returns`          | 43    |

320 nodes, 319 edges, precision and recall 1.00 against the reference.

### 3. What is missing

The last line: links between devices in the tree **0**, in the gold graph
**123**. The data models say what each device contains. Which bay a robot
serves, which alarm stops which cell, which incident happened where: none of
it is in the YAML. Those links are in the prose (EXE03).
