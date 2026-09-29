# EXE00 — A solved example

**MCP concept:** the whole loop, end to end, on a server that already works.
There is nothing to write here. Sections 3 and 4 of the
[unit README](../../README.md) walk through it step by step.

`exe00.py` exposes two tools, `inventory_count` and `project_code`, over data
the model cannot guess.

## Try every command

```bash
uv run python exercises/exe00-demo/check.py              # tools/list + tools/call, no LLM
uv run python exercises/exe00-demo/exe00.py --inspect    # what a host discovers
uv run python exercises/exe00-demo/exe00.py              # the model answers PROMPT
uv run python exercises/exe00-demo/exe00.py --verbose    # full HOST/OLLAMA/MCP trace
uv run python exercises/exe00-demo/exe00.py --show-raw   # the prompt the model receives
uv run python exercises/exe00-demo/exe00.py --prompt "Give me the Atlas project code and the stock count for servo-x12."
```

## Think about it

- Where in the `--verbose` trace does the model stop and the host take over?
- Ask for project `zeus`. What does the model receive, and what does it answer?
- Every other exercise file has the same shape as this one: the `mcp` object,
  a `PROMPT`, some data, tools, and `run(mcp, PROMPT, __file__)`. Only the
  tools change.
