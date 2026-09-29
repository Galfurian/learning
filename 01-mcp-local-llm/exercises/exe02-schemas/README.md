# EXE02 — Input and output schemas

**MCP concept:** the JSON Schema of a tool is the contract. Python type hints
become that schema: defaults become optional arguments, `Literal` becomes an
`enum`, and a Pydantic return type becomes an `outputSchema` with structured
content.

## Task

In `exe02.py`, write a tool `find_trains` that searches the `TIMETABLE`.

Input:

| Argument        | Type                                  | Required | Default   |
|-----------------|---------------------------------------|----------|-----------|
| `origin`        | string                                | yes      |           |
| `destination`   | string                                | yes      |           |
| `departs_after` | string, 24h `HH:MM`                   | no       | `"00:00"` |
| `kind`          | one of `regional`, `high-speed`, `any`| no       | `"any"`   |

Output: a list of trains ordered by departure time. Each train has exactly
`number`, `departs` and `kind`. Define it as a Pydantic model `Train`.

City names must match regardless of case (`"Verona"` and `"verona"` are the
same city). Times in `HH:MM` format compare correctly as strings.

## Verify

```bash
uv run python exercises/exe02-schemas/check.py
uv run python exercises/exe02-schemas/exe02.py --inspect
uv run python exercises/exe02-schemas/exe02.py --verbose
```

In `--inspect`, compare the `input schema` and `output schema` lines with your
Python signature.

## Hints

- `from typing import Literal` and `from pydantic import BaseModel`.
- The return annotation `-> list[Train]` is enough for the SDK to publish an
  output schema that describes every field of a train. Without a return
  annotation, the tool has no output schema.

## Think about it

- Call the tool with `kind="bus"` (the check does this). Your function never
  runs. Who rejected the call, and what error text comes back?
- The model never sees your Python code. Which fields of the schema help it
  pick `high-speed` and `09:00` from the user's sentence?
- In the `--verbose` trace, compare the MCP result with the `role=tool`
  message. What does the host do with structured content?
