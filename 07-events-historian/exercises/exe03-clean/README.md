# EXE03 — What is a change

**Concept:** a subscription sends the current value first (the state, not an
event), may send the same value twice, and starts again when the replay
restarts.

## Task

Implement `clean(changes)`.

```bash
uv run python exercises/exe03-clean/check.py
uv run python exercises/exe03-clean/exe03.py
uv run python exercises/exe03-clean/exe03.py --fixture
```

## What to look at

Measured on the real recording: 2,258 changes in, 2,177 kept, 81 initial
values (one per signal), **no duplicates**. On the fixture, the duplicate,
the unchanged value and the replay restart are there on purpose: the
cleaning needs to handle what the real line did not show this time.
