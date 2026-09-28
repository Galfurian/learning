# 01 — MCP server + small local LLM

Goal: build a real MCP server, discover its tools from a host, expose those tools to a small local LLM, execute the model's tool calls through MCP, and feed the results back to the model.

The example deliberately avoids LangChain/LlamaIndex/etc. The interesting mechanism should remain visible.

## What you will build

```text
Ollama model
    ^   |
    |   | function call
    |   v
src/agent.py              <-- host / adapter
    ^   |
    |   | MCP over stdio
    |   v
src/server.py             <-- MCP server
```

The MCP server has demo data the model cannot infer reliably on its own:

- lab inventory counts
- internal demo project codes

## Prerequisites

Inside WSL:

- Python 3.11+
- `uv`
- Ollama reachable at `http://localhost:11434`
- an Ollama model with tool-calling support

The examples default to `qwen3:1.7b` so the exercise also works on modest laptops. You can pass another installed tool-capable model with `--model`.

## 0. Clone the learning repo

```bash
git clone git@github.com:Galfurian/learning.git
cd learning/01-mcp-local-llm
```

## 1. Install the Python workspace

With `uv`:

```bash
uv sync
```

If you do not have uv yet:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
exec $SHELL
uv sync
```

## 2. Prepare Ollama

Ollama setup is shared knowledge, so the complete WSL/Linux installation and server guide lives in [../docs/ollama.md](../docs/ollama.md).

For this unit the minimum sequence is:

```bash
# Install once, if needed
curl -fsSL https://ollama.com/install.sh | sh

# Start the API server only if it is not already running
ollama serve
```

Keep `ollama serve` running in that terminal. In another terminal:

```bash
curl http://localhost:11434/api/tags
ollama pull qwen3:1.7b
```

If the curl command already works before you run `ollama serve`, a service is already providing Ollama and you do not need to start a second server.

## 3. First understand MCP without an LLM

Run:

```bash
uv run python src/inspect_mcp.py
```

This program launches `src/server.py` as a subprocess, connects to it over MCP stdio, lists the tools, prints their JSON schemas, then directly calls one tool.

You should see tools named:

```text
inventory_count
project_code
```

This step matters: MCP works independently of the LLM.

You can also inspect the server interactively with the official MCP Inspector:

```bash
uv run mcp dev src/server.py
```

## 4. Let the local LLM use the MCP tools

Run:

```bash
uv run python src/agent.py
```

The default prompt is:

```text
What is the internal code for project atlas?
```

The useful part of the output should look conceptually like:

```text
MCP tools: inventory_count, project_code
[step 1] tool call -> project_code({'project': 'atlas'})
[step 1] tool result <- ...A7-KAPPA...

Assistant: ...
```

Try another question:

```bash
uv run python src/agent.py "How many flux-capacitor units are currently in the lab?"
```

Or force multiple tools:

```bash
uv run python src/agent.py "Give me the Atlas project code and the stock count for servo-x12."
```

## 5. Read the code in this order

1. `src/server.py` — two ordinary Python functions become MCP tools.
2. `src/inspect_mcp.py` — MCP discovery and invocation without any LLM.
3. `src/agent.py::to_ollama_tool` — translates an MCP tool description into an Ollama function schema.
4. `src/agent.py::run_agent` — the tool-calling loop.
5. `docs/mental-model.md` — put the pieces into the right conceptual boxes.
6. `exercises/README.md` — modify the system yourself.

## Files

```text
01-mcp-local-llm/
├── README.md
├── pyproject.toml
├── src/
│   ├── server.py
│   ├── inspect_mcp.py
│   └── agent.py
├── docs/
│   └── mental-model.md
└── exercises/
    └── README.md
```

## The key lesson

MCP and LLM tool calling solve different halves of the problem:

- **MCP** standardizes how a host discovers and invokes external capabilities.
- **Tool calling** lets the model emit a structured request saying which capability it wants and with which arguments.
- **The host** connects the two worlds and owns execution.

Once this unit is clear, the natural next unit is to remove one simplification at a time: resources/prompts, Streamable HTTP, multiple MCP servers, permissions, or a more capable agent loop.
