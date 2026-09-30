# Exercises

Each exercise is one folder with three files:

```text
exeNN-topic/
├── README.md   # the task, and what MCP concept it teaches
├── exeNN.py    # the file you edit: an MCP server with a TODO and a fixed prompt
└── check.py    # verifies your server over MCP, without any LLM
```

Start with `exe00-demo`: it is already solved, so you can read a working server
and try every command before writing your own. Then do the others in order.
Each one adds a single MCP concept. `exe07-factory-cell` is a solved demo
again: it puts everything together on a longer task.

| #  | Folder                                    | MCP concept                                      |
|----|-------------------------------------------|--------------------------------------------------|
| 00 | [exe00-demo](exe00-demo/)                 | solved example: read, run, trace; nothing to write |
| 01 | [exe01-first-tool](exe01-first-tool/)     | register a tool; docstring and types become the contract |
| 02 | [exe02-schemas](exe02-schemas/)           | defaults, enums, structured output (`outputSchema`) |
| 03 | [exe03-errors-state](exe03-errors-state/) | `isError` results, `ToolError`, server state     |
| 04 | [exe04-chaining](exe04-chaining/)         | one tool's output is the next tool's input; the host loop |
| 05 | [exe05-resources](exe05-resources/)       | resources: context the host chooses, not the model |
| 06 | [exe06-on-demand-resources](exe06-on-demand-resources/) | exposed is not loaded: the host reads a resource only when needed |
| 07 | [exe07-factory-cell](exe07-factory-cell/)  | demo: simulated factory logs, many rounds, context budget, thinking |

## How one exercise file works

`exeNN.py` is the MCP server and the host at the same time:

```text
uv run python exeNN.py              HOST: starts "exeNN.py --serve" as a child process,
                                    connects over MCP stdio, and runs the Ollama loop
uv run python exeNN.py --serve      MCP SERVER over stdio (the host does this for you)
```

The host part is shared code in `src/mcplab/`. You only write the server part.

Each `exeNN.py` gives you the function signatures. Your job is to implement
the functions and **register** them on the `mcp` server object with a
decorator (`@mcp.tool()`, or `@mcp.resource(...)` in EXE05) or with
`mcp.add_resource(...)` (EXE06). Registering is
what "exposing" means: the server then lists the function over MCP and runs it
when a client asks. An unregistered function is ordinary Python that no client
can see.

## Commands

Run from the unit folder (`01-mcp-local-llm/`):

```bash
uv run python exercises/exe01-first-tool/check.py              # verify, no LLM
uv run python exercises/exe01-first-tool/exe01.py --inspect    # what a host discovers
uv run python exercises/exe01-first-tool/exe01.py              # the model answers PROMPT
uv run python exercises/exe01-first-tool/exe01.py --verbose    # full HOST/OLLAMA/MCP trace
uv run python exercises/exe01-first-tool/exe01.py --show-raw   # the prompt the model receives
uv run python exercises/exe01-first-tool/exe01.py --think      # let the model reason first
uv run python exercises/exe01-first-tool/exe01.py --think --show-thinking  # and show all of it
uv run python exercises/exe01-first-tool/exe01.py --num-ctx 16384  # context window in tokens
uv run python exercises/exe01-first-tool/exe01.py --prompt "..."  # ask something else
uv run mcp dev exercises/exe01-first-tool/exe01.py             # official MCP Inspector
```

## Solutions

Reference solutions are in [solutions/](solutions/). Try first. To check a
solution, pass its path to the check:

```bash
uv run python exercises/exe01-first-tool/check.py exercises/solutions/exe01.py
```

## Extra

When the six exercises are clear, try these on your own. There is no scaffold.

1. **Two tools, one question.** Put the EXE02 and EXE03 tools in one server and
   ask something that needs both. Does the model call them in parallel or in
   separate steps?
2. **HTTP transport.** Run one exercise server with Streamable HTTP and change
   only the client connection target. Tool semantics and transport are separate.
3. **Remove Ollama.** Write a fake "model" that always returns a call to
   `project_code(project="atlas")` of EXE00. MCP and tool calling are independent.
4. **Prompts.** Add an `@mcp.prompt()` to EXE05 and let the host build the user
   message from `prompts/get` with `run(..., mcp_prompt=(name, arguments))`.
   EXE07 shows a working example. This completes the tool/resource/prompt triad.
