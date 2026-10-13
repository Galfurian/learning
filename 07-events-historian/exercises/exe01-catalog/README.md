# EXE01 — The catalog: subscribe only to what moves

**Concept:** a line exposes thousands of variables; a recording changes a
few hundred. A collector subscribes to those, not to everything.

## Task

Implement `select_nodes(nodes)`: variables only, with events in the trace,
most events first.

```bash
uv run python exercises/exe01-catalog/check.py
```

## Run (lab tailnet only; the check above runs offline)

```bash
export ICE_SIM_URL=http://<host>:<port>
uv run python exercises/exe01-catalog/exe01.py
```

Measured on `lab-session` (logical machine names):

| machine | nodes | with data | mapped signals |
|---------|-------|-----------|----------------|
| conveyor | 1,979 | 161 | 47 |
| mill_cell | 328 | 69 | 4 |
| assembly_cell | 1,082 | 15 | 7 |
| screwdriver | 359 | 8 | 3 |
| qc_station | 11 | 7 | 5 |
| storage | 29 | 5 | 4 |
| robot_a, robot_b | 38 each | 4 each | 4 each |
| tester | 8 | 3 | 3 |

- 3,872 nodes on the nine servers, 276 with data. The assembly cell has 1,082 nodes and 15
  that move: its robots' state is mostly not recorded.
- The mapped signals are fewer still: the unit maps what its rules read.
  The rest is not lost; it is not used yet.
