# EXE02 — When did it happen

**Concept:** an event needs a time on the line, not the time a server wrote a
value. The collector polls the replay position every 0.5 s and places each
notification between the two polls around it: an interpolated time and its
bounds.

## Task

Implement `place(wall, polls)`.

```bash
uv run python exercises/exe02-event-time/check.py
uv run python exercises/exe02-event-time/exe02.py
```

## What to look at

The table shows your `place()` on four polls. Then the bound widths of the
two cached recordings. Measured:

| recording | median bound width | max |
|-----------|--------------------|-----|
| speed 1   | 0.52 s | 0.67 s |
| speed 10  | 5.15 s | 5.34 s |

At speed 10 two events 3 s apart can have overlapping bounds: their order is
not known. Durations and orders are measured on the speed 1 recording.
