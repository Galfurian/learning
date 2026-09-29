# EXE06 — Resources loaded on demand

**MCP concept:** a resource the server *exposes* is not a resource the model
*sees*. Exposing puts a URI and a description in `resources/list`. Loading
means someone sends `resources/read` and puts the content into the model's
context. These are two separate events, and the host controls both.

In EXE05 the host attached two resources up front, before the model saw the
question. That is simple, but it does not scale: with fifty manuals, every
request would carry all fifty in the prompt.

Here the host does something else:

1. It sends `resources/list` and puts only the catalog (URI + description)
   in the system message. No content.
2. It gives the model one extra tool, `read_resource(uri)`. This tool belongs
   to the **host**, not to the MCP server: it does not appear in `tools/list`.
3. When the model calls `read_resource`, the host sends MCP `resources/read`
   and appends the content as a `role=tool` message. Only now is that manual
   in the model's context.

```text
model calls read_resource(uri)      <- host tool, Ollama tool-calling format
host sends resources/read(uri)      <- MCP, host -> server
```

Compare with EXE03: there the model's call became MCP `tools/call`. Here it
becomes `resources/read`. The server does not know or care why the host read it.

See `run_agent(..., on_demand_resources=True)` in `src/mcplab/agent.py`.

## Before you start

```bash
uv run python exercises/exe06-on-demand-resources/exe06.py
```

The server exposes no manuals yet. The catalog is empty, so the model has
nothing to load. It may still try a made-up URI and get an error back.

## Task

`exe06.py` contains four manuals in `MANUALS`, each with a short `summary` and
a long `text`. Register every manual as a **static resource**:

- URI: `lab://manuals/<machine>`, for example `lab://manuals/laser-cutter`
- description: the manual's `summary`
- content: the manual's `text`

There are four of them, so do not write four decorated functions. Register
them in the loop that is already in the file, with `mcp.add_resource(...)`
and `TextResource`:

```python
from mcp.server.mcpserver.resources import TextResource
```

`TextResource` takes `uri`, `name`, `description` and `text`. Do not add tools.

## Verify

```bash
uv run python exercises/exe06-on-demand-resources/check.py
uv run python exercises/exe06-on-demand-resources/exe06.py --inspect
uv run python exercises/exe06-on-demand-resources/exe06.py
```

The run ends with a summary like:

```text
Resources exposed by the server: 4 static (lab://manuals/laser-cutter, ...)
Resources loaded into the model's context: 1 (lab://manuals/laser-cutter)
```

Now ask other questions and watch the second line change:

```bash
uv run python exercises/exe06-on-demand-resources/exe06.py --prompt "What bandwidth does the oscilloscope have?"
uv run python exercises/exe06-on-demand-resources/exe06.py --prompt "Which nozzle temperature should I use for PETG?"
uv run python exercises/exe06-on-demand-resources/exe06.py --prompt "Hi! Who are you?"
```

The last one needs no manual: four exposed, zero loaded.

## See it happen

```bash
uv run python exercises/exe06-on-demand-resources/exe06.py --verbose
```

- Before step 1: `resources/list` returns only metadata. Open the step 1
  `role=system` bubble: it has the catalog, not the manuals.
- In step 1 the model calls `read_resource`, and `resources/read` follows.
- In step 2 the manual is in the conversation as a `role=tool` message.

## Think about it

- The model picks a manual only from its description. Write a vague summary
  (for example `"Manual."`) for the laser cutter and ask the acrylic question
  again. What does the model load now?
- Who could still read a manual without the model asking? Would that be wrong?
- EXE05 used `attach=`, EXE06 uses `on_demand_resources=True`. List what each
  costs: prompt size, number of steps, and the risk that the model loads the
  wrong document or none.
