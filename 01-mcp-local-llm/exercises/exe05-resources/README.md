# EXE05 — Resources: context chosen by the host

**MCP concept:** MCP has more than tools. Who decides to use each primitive:

| Primitive | Controlled by | Example                         |
|-----------|---------------|---------------------------------|
| Tool      | the model     | `book_room`, the model calls it |
| Resource  | the host/app  | a document the host attaches    |
| Prompt    | the user      | a template picked from a menu   |

A resource is data identified by a URI. The model cannot request it. The host
reads it with `resources/read` and decides where to put it. Here the host puts
it in the system message (see `attach=[...]` at the bottom of `exe05.py`).

## Before you start

```bash
uv run python exercises/exe05-resources/exe05.py
```

The resources do not exist yet, so the host attaches nothing. Read the model's
answer: it has no rules to follow.

## What "expose" means

Resources are part of MCP, exactly like tools. They are just a different MCP
primitive, with their own protocol operations:

```text
Tools                        Resources
-----                        ---------
tools/list                   resources/list, resources/templates/list
tools/call   (name + args)   resources/read   (URI)
@mcp.tool()                  @mcp.resource("some://uri")
```

To expose something means to register it on the MCP server, so that a client
can find it with a `.../list` request and use it with the matching request.
A plain Python variable such as `RULES` is invisible to the client. Once a
function returning `RULES` is registered with `@mcp.resource("lab://rules")`,
the server lists `lab://rules` and answers `resources/read` for that URI by
calling the function.

The difference from a tool is who triggers the call. The host sends
`tools/call` because the model asked for it. The host sends `resources/read`
because the host itself decided to (here, because of `attach=[...]`).

## Task

`exe05.py` already contains the signatures of two functions. Implement both
and register them as MCP resources:

1. `lab_rules()` returns `RULES`. Register it as a **static resource** with
   URI `lab://rules`: one fixed URI, so the function takes no arguments.
2. `machine_notes(machine)` returns the notes from `MACHINES`. Register it as a
   **resource template** with URI `lab://machines/{machine}`: one function
   serves every machine, and the `{machine}` part of the URI becomes the
   function argument. An unknown machine is an error.

Give both a description and the MIME type `text/plain`. Do not add tools.

## Verify

```bash
uv run python exercises/exe05-resources/check.py
uv run python exercises/exe05-resources/exe05.py --inspect
uv run python exercises/exe05-resources/exe05.py --verbose
```

In `--verbose`, find the `resources/read` panels. They happen before the first
model step, and the model is never asked.

## Hints

- The decorator is `@mcp.resource("uri", description=..., mime_type=...)`.
- A static resource function takes no arguments. A template function takes one
  argument for each `{placeholder}` in the URI.

## Think about it

- `MCP tools:` is empty, yet the model answers correctly. Why is this not tool
  calling?
- What changes if you turn `lab_rules` into a tool instead? Who decides when to
  read the rules then?
- Change `attach=` to read `lab://machines/3d-printer` instead. Ask a question
  about the laser cutter with `--prompt`. The host controls what the model knows.
