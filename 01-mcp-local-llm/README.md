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

The two key protocol operations demonstrated here are:

```text
MCP protocol        Python SDK
------------        ----------
tools/list          client.list_tools()
tools/call          client.call_tool(...)
```

So the host first discovers the server's tools through `tools/list`, then invokes one through `tools/call`. The SDK methods above are the Python interface to those protocol operations.

You should see tools named:

```text
inventory_count
project_code
```

This step matters: MCP works independently of the LLM. The detailed explanation is in [docs/mental-model.md](docs/mental-model.md).

You can also inspect the server interactively with the official MCP Inspector:

```bash
uv run mcp dev src/server.py
```

## 4. Let the local LLM use the MCP tools

The agent intentionally has **no default prompt**. A prompt is always required:

```bash
uv run python src/agent.py "What is the internal code for project atlas?"
```

Running `uv run python src/agent.py` without a prompt prints usage instead of silently choosing a question for you.

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

### See the inner workings

Use `--verbose` to make the adapter loop visible:

```bash
uv run python src/agent.py --verbose "What is the internal code for project atlas?"
```

Verbose mode starts by defining the actors used in the trace:

- **HOST** — `src/agent.py`, which orchestrates the loop and owns conversation history;
- **OLLAMA** — the local runtime/API that runs the model; the **model** decides whether to emit `tool_calls` and with which arguments, and Ollama returns that output to the host;
- **MCP SERVER** — `src/server.py`, which exposes and executes tools.

Conversation roles such as `system`, `user`, `assistant`, and `tool` are message roles, not separate actors.

Every Rich panel title is standardized to only show communication direction, for example `HOST -> OLLAMA` or `HOST -> MCP SERVER`. The first line inside the panel says what is happening, such as `Event: conversation message · role=user` or `Event: MCP tools/call · project_code`.

Each `STEP N` divider also explains its participants and purpose. A step means **one Ollama inference round plus any MCP tool execution requested by that round**. The next step begins only when HOST calls Ollama again, typically after appending a `role=tool` result to the conversation.

Verbose mode is intentionally **not** a raw SDK dump. It keeps the parts that explain the architecture:

- the `tools/list` discovery and a compact table of discovered tools;
- every message sent to Ollama, rendered as a colored bubble;
- the assistant's structured `tool_calls`;
- the arguments sent through MCP `tools/call`;
- the meaningful MCP result that becomes the next `role=tool` message.

Noise such as SDK metadata, null fields, repeated tool schemas, and repeated request metadata is hidden.

The second Ollama request is especially useful to inspect: it shows the original user message, the assistant tool-call message, and the new `role=tool` message together in the exact conversation history that goes back to the model.

Normal mode keeps only the high-level tool-call trace and final answer.

### See what the model actually receives

Use a separate mode when you want to inspect the text below the chat/message abstraction:

```bash
uv run python src/agent.py --show-raw "What is the internal code for project atlas?"
```

This mode does **not** mix the protocol trace with the model input. For each inference round it prints only the rendered prompt string produced by Ollama's chat template, then lets the normal agent continue silently until the next model invocation.

So with one tool call you will normally see two rendered prompts:

1. step 1: system message + user message + tool definitions;
2. step 2: the same conversation, now extended with the assistant tool call and the tool result.

This is the actual rendered prompt string immediately before tokenization. The transformer ultimately receives token IDs, and model-specific BOS handling may happen separately from the rendered string.

Implementation note: this learning aid uses Ollama's internal `_debug_render_only` request option to obtain `_debug_info.rendered_template`. It is intentionally isolated in `src/model_io.py` because it is a debug/internal interface and may change across Ollama versions.

`--verbose` and `--show-raw` are mutually exclusive so the two conceptual layers remain separate.

The source is split by responsibility on purpose: `agent.py` contains the orchestration loop, `bridge.py` contains MCP/Ollama conversion helpers, `model_io.py` contains low-level model-input inspection, and `ui.py` contains Rich rendering. This keeps the learning target visible when you open `agent.py`.

## 5. Read the code in this order

1. `src/server.py` — two ordinary Python functions become MCP tools.
2. `src/inspect_mcp.py` — MCP discovery and invocation without any LLM.
3. `docs/mental-model.md` — understand `tools/list`, `tools/call`, and the host/model/server separation.
4. `src/bridge.py` — translates MCP tool definitions/results into Ollama's tool-calling format.
5. `src/agent.py::run_agent` — the actual orchestration loop, now kept deliberately small.
6. `src/model_io.py` — asks Ollama to expose the rendered prompt string used as model input.
7. `src/ui.py` — Rich rendering for the observation modes; useful for learning, but not part of the agent logic.
8. `exercises/README.md` — modify the system yourself.

## Files

```text
01-mcp-local-llm/
├── README.md
├── pyproject.toml
├── src/
│   ├── server.py
│   ├── inspect_mcp.py
│   ├── agent.py
│   ├── bridge.py
│   ├── model_io.py
│   └── ui.py
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
