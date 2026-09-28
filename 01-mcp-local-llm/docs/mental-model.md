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

The interesting code in this unit is the small adapter loop in `src/agent.py`:

1. MCP `tools/list` is exposed by the Python SDK as `list_tools()`.
2. `to_ollama_tool()` maps each discovered MCP tool description to Ollama's function schema.
3. The local model chooses whether to call a tool.
4. The host sends that call through MCP `tools/call`, exposed by the SDK as `call_tool()`.
5. The host adds the tool result back to the LLM conversation.
6. The loop ends when the model returns an answer without another tool call.

This is the minimal architecture behind many agent frameworks.

## Why stdio first?

For a local MCP server, stdio removes networking from the exercise. The host starts the server process and the MCP protocol travels over the child's stdin/stdout. Once the mental model is clear, the same server idea can be moved to Streamable HTTP.
