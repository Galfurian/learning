# Mental model: MCP + tool calling

The runtime trace uses three software actors. Keeping them separate is the main point of this unit.

- **HOST** — `src/agent.py`. It owns the orchestration loop and conversation history.
- **OLLAMA** — the local model runtime/API. It runs the selected LLM. The model decides whether to emit `tool_calls` and chooses their arguments; Ollama returns that model output to the host.
- **MCP SERVER** — `src/server.py`. It exposes tool contracts and executes tools requested through MCP.

The words `system`, `user`, `assistant`, and `tool` are **conversation roles**, not additional software actors.

```text
HOST                         OLLAMA
 |--- messages + tools ------->|
 |<-- assistant/tool_calls ----|
 |
 |         MCP over stdio
 |--- tools/call -----------> MCP SERVER
 |<-- tool result -----------|
 |
 |--- updated messages -------> OLLAMA
 |<-- final assistant ---------|
```

In verbose mode, panel titles contain only the direction between actors, such as `HOST -> OLLAMA`. The first line inside each panel states the event being shown.

A `STEP` is one model-inference round. HOST sends the current conversation to OLLAMA; if the model requests a tool, HOST executes that request through the MCP SERVER as part of the same step. A new step starts only when HOST invokes OLLAMA again with the updated conversation.

## 1. MCP server

`src/server.py` owns capabilities. It does **not** know Ollama exists.

It exposes typed Python functions with `@mcp.tool()`. The MCP SDK derives the tool name, description, and JSON input schema from the function, its docstring, and its annotations.

## 2. MCP client / host

`src/agent.py` is the host. It launches the MCP server as a child process and connects over stdio.

The host asks the server which tools exist, then invokes a tool when needed. This separation is important: MCP defines how the host discovers and calls capabilities; it is not an LLM inference API.

## Protocol operations vs Python SDK methods

The MCP protocol names and the Python SDK method names are related, but they are not the same thing.

```text
MCP protocol        Python SDK
------------        ----------
tools/list          client.list_tools()
tools/call          client.call_tool(...)
```

### `tools/list`: discover the server's tools

The host does not need to hard-code which tools a server exposes.

At the protocol level, the client sends a `tools/list` request. The server returns a list of tool definitions. Each definition includes the information needed to understand and call the tool, notably:

- tool name;
- description;
- JSON Schema for the input arguments.

In our Python code, the SDK hides the raw protocol message behind:

```python
page = await client.list_tools()
```

That call corresponds to MCP `tools/list`.

This is why adding a new `@mcp.tool()` to `src/server.py` does not require adding its name manually to `src/agent.py`: the host discovers it.

### `tools/call`: invoke one discovered tool

Once the host knows a tool exists, it can invoke it by name with arguments.

At the protocol level this is a `tools/call` request.

In our Python code:

```python
result = await client.call_tool(
    "project_code",
    {"project": "atlas"},
)
```

corresponds to MCP `tools/call`.

The important separation is:

```text
MCP server
    exposes tool definitions
          |
          | tools/list
          v
Host
    learns name + description + schema
          |
          | gives schemas to the LLM
          v
LLM
    chooses a tool + arguments
          |
          v
Host
          |
          | tools/call
          v
MCP server
    executes the actual Python function
```

The LLM itself is not speaking MCP in this exercise. The host speaks MCP to the server and separately speaks Ollama's tool-calling format to the model.

## 3. Local LLM

Ollama receives the conversation plus a list of function schemas. A tool-capable model may answer normally or emit a structured tool call containing a function name and arguments.

The model does not execute the function itself.

## 4. The adapter loop

The orchestration loop lives in `src/agent.py`. Format conversion lives in `src/bridge.py`, while all Rich tracing lives in `src/ui.py`. This separation is intentional: opening `agent.py` should show the agent mechanics, not presentation code.

The loop is:

1. MCP `tools/list` is exposed by the Python SDK as `list_tools()`.
2. `to_ollama_tool()` maps each discovered MCP tool description to Ollama's function schema.
3. The local model chooses whether to call a tool.
4. The host sends that call through MCP `tools/call`, exposed by the SDK as `call_tool()`.
5. The host adds the tool result back to the LLM conversation.
6. The loop ends when the model returns an answer without another tool call.

This is the minimal architecture behind many agent frameworks.

## Observe the loop with `--verbose`

The implementation can expose this flow at runtime:

```bash
uv run python src/agent.py --verbose "What is the internal code for project atlas?"
```

The trace uses colored Rich panels, but it deliberately filters SDK noise rather than dumping every object verbatim. `tools/list` is summarized as the discovered tool contract; `tools/call` shows the arguments and meaningful result; every LLM conversation message is shown as a separate role-colored bubble.

This matters because tool calling is a **multi-message conversation**. After a tool executes, the host does not magically modify the previous answer: it appends a new `role=tool` message and calls the model again. In verbose mode you can inspect the complete message list sent on each Ollama request and see that history grow step by step.

The trace therefore exposes MCP discovery, schema translation into Ollama's tool format, the model's structured tool request, MCP `tools/call`, the returned value, the appended tool message, and the next model invocation.

Without `--verbose`, the same code path runs but these adapter details stay hidden.

## One level lower: the rendered model input

The `messages` and `tools` objects are still not what the transformer directly consumes. Ollama applies the model's chat template and produces a single rendered prompt string. That string is then tokenized for the model.

Conceptually:

```text
HOST
  |
  | messages + tools
  v
OLLAMA
  |
  | apply chat template
  v
rendered prompt string
  |
  | tokenize
  v
MODEL token IDs
```

The separate inspection mode shows that intermediate rendered string:

```bash
uv run python src/agent.py --show-model-input "What is the internal code for project atlas?"
```

It intentionally does not show the normal verbose protocol panels. Each model-inference round gets its own rendered prompt, so a tool-calling interaction normally exposes the pre-tool prompt and then the second prompt containing the assistant tool call plus the tool result.

This is the exact rendered prompt string returned by Ollama immediately before tokenization, not the final token-ID sequence. Some model-specific special-token handling, such as a leading BOS token, can be applied separately by the runner.

The implementation lives in `src/model_io.py` and uses Ollama's internal `_debug_render_only` facility. It is a learning/debug hook rather than a stable public API.

## Why stdio first?

For a local MCP server, stdio removes networking from the exercise. The host starts the server process and the MCP protocol travels over the child's stdin/stdout. Once the mental model is clear, the same server idea can be moved to Streamable HTTP.
