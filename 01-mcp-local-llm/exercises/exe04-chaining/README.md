# EXE04 — Chaining tools

**MCP concept:** tools are small and composable. The output of one tool is the
input of the next, and the host loop (not MCP) makes that possible: one
inference round per step, results appended to the conversation, repeat.

## Task

`exe04.py` already contains the `Course` model and the signatures of two
functions. Implement both and register them as MCP tools:

1. `find_student(full_name)` returns the student ID (for example
   `"VR-48213"`). The name match ignores case and extra spaces. An unknown
   name is a `ToolError`.
2. `student_courses(student_id)` returns the student's courses. Each course
   has `code`, `title` and `room`. An unknown ID is a `ToolError` that tells
   the model to call `find_student` first.

The model cannot guess `VR-48213`: it has to call `find_student`, read the
result, then call `student_courses` in a later step.

## Verify

```bash
uv run python exercises/exe04-chaining/check.py
uv run python exercises/exe04-chaining/exe04.py --verbose
```

## Watch a small model fail

With `qwen3:1.7b`, the normal run often fails. In step 1 the model emits
**both** calls at once and invents the ID for the second one, because it
cannot see the first result yet. Your error message comes back, and the model
may or may not recover.

Now let the model reason before it acts:

```bash
uv run python exercises/exe04-chaining/exe04.py --think --verbose
```

Count the steps in the trace. Each `STEP` is one call to Ollama.

## Think about it

- Where does the sequencing live: in MCP, in the host, or in the model?
- Tool descriptions are the only hint the model has. Write in the docstrings
  which tool produces the ID and which tool needs it. Does the plain run get
  better?
- A tool `rooms_for_student(full_name)` would remove the chain. When is a
  bigger tool the better design for a small model?
