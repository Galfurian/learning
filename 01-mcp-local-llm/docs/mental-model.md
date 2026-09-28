# Mental model: MCP + tool calling

There are four different actors. Keeping them separate is the main point of this unit.

```text
User
  |
  v
Host / src/agent.py
  |                         Ollama
  |--- tools schema -------> local LLM
  |<-- tool call -----------|
  |
  |        MCP over stdio
  |--- tools/call ---------> src/server.py
  |<-- tool result ---------|
  |
  |--- tool result --------> local LLM
  |<-- final answer --------|
  v
User
```

## 1. MCP server

`src/server.py` owns capabilities. It does **not** know Ollama exists.

It exposes typed Python functions with `@mcp.tool()`. The MCP SDK derives the tool name, description, and JSON input schema from the function, its docstring, and its annotations.

## 2. MCP client / host

`src/agent.py` is the host. It launches the MCP server as a child process and connects over stdio.

The host asks the server which tools exist, then invokes a tool when needed. This separation is important: MCP defines how the host discovers and calls capabilities; it is not an LLM inference API.

## 3. Local LLM

Ollama receives the conversation plus a list of function schemas. A tool-capable model may answer normally or emit a structured tool call containing a function name and arguments.

The model does not execute the function itself.

## 4. The adapter loop

The interesting code in this unit is the small adapter loop in `src/agent.py`:

1. MCP `list_tools()` returns MCP tool descriptions.
2. `to_ollama_tool()` maps each MCP description to Ollama's function schema.
3. The local model chooses whether to call a tool.
4. The host sends that call to MCP with `call_tool()`.
5. The host adds the tool result back to the LLM conversation.
6. The loop ends when the model returns an answer without another tool call.

This is the minimal architecture behind many agent frameworks.

## Why stdio first?

For a local MCP server, stdio removes networking from the exercise. The host starts the server process and the MCP protocol travels over the child's stdin/stdout. Once the mental model is clear, the same server idea can be moved to Streamable HTTP.
