# EXE01 — Your first MCP tool

**MCP concept:** a tool is a Python function the server registers. The SDK turns
its name, docstring and type hints into the contract that `tools/list` returns.

## Before you start

Run the exercise as it is:

```bash
uv run python exercises/exe01-first-tool/exe01.py
```

The server exposes no tools yet (`MCP tools:` is empty), so the model has to
count letters by itself. Run it two or three times: small models are bad at
counting characters and the answer changes between runs.

## Task

In `exe01.py`, write a function `count_letter(word, letter)` that returns how
many times `letter` appears in `word`, ignoring case. Register it as an MCP
tool on the `mcp` server object.

Requirements:

- tool name: `count_letter`
- arguments: `word` (string) and `letter` (string), both required
- result: an integer
- a docstring that tells the model what the tool does and what each argument means

## Verify

1. Check the contract without any LLM:

   ```bash
   uv run python exercises/exe01-first-tool/check.py
   ```

2. Look at what a host discovers:

   ```bash
   uv run python exercises/exe01-first-tool/exe01.py --inspect
   ```

3. Let the model use it, and watch every message:

   ```bash
   uv run python exercises/exe01-first-tool/exe01.py
   uv run python exercises/exe01-first-tool/exe01.py --verbose
   ```

## Hints

- Registration is a decorator on the server object: `@mcp.tool()`.
- Look at `exercises/exe00-demo/exe00.py` for a working example.

## Think about it

- Delete the docstring and run `--inspect` again. What does the model see now?
- Rename the Python function. What happens to the tool name?
- Change `word: str` to `word: int`. Which part of the stack rejects the call?
- Run with `--show-raw`: where does your docstring end up in the model's prompt?
