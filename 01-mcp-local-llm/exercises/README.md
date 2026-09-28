# Exercises

Do these in order.

## 1. Add one tool

Add this capability to the MCP server in `src/server.py` without touching `src/agent.py`:

- tool name: `machine_status`
- input: machine name
- output: one of `idle`, `running`, `offline`

Then run:

```bash
uv run python src/inspect_mcp.py
```

The new tool should appear automatically.

**Point:** the host discovers the contract; you should not need to hard-code the new function in the agent.

## 2. Force a two-tool question

Ask something that requires two different MCP tools, for example:

```text
Tell me the Atlas project code and how many servo-x12 units are in stock.
```

Observe whether the model emits parallel calls or calls them over multiple loop iterations.

## 3. Break the schema

Temporarily change the type of `inventory_count(part: str)` to something incompatible or call it with a missing argument from `src/inspect_mcp.py`.

Observe where validation happens and what the MCP error looks like.

## 4. Add an HTTP transport

After the stdio version is clear, run the same MCP server using Streamable HTTP and change only the client connection target.

**Point:** tool semantics and transport are separate concerns.

## 5. Remove Ollama

Write a tiny fake 'model' under `src/` that always returns a call to `project_code(project="atlas")`.

**Point:** prove to yourself that MCP and tool calling are independent. Ollama is only one possible model runtime.
