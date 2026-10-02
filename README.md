# learning

Repository of small, self-contained learning units.

The rule is simple: one topic = one folder = one runnable workspace.

## Layout

```text
learning/
├── README.md
├── .gitignore
├── docs/                  # reusable knowledge shared by multiple units
│   └── ollama.md
└── NN-topic-name/
    ├── README.md
    ├── pyproject.toml
    ├── src/               # runnable source code
    ├── docs/              # knowledge specific to this unit
    └── exercises/
```

Each unit should contain:

- **README.md** — learning path, commands, and expected results.
- **workspace** — the smallest runnable project that demonstrates the topic.
- **src/** — executable/source code for the unit.
- **docs/** — concepts specific to that unit.
- **exercises/** — small changes to make without copying a solution blindly.

Reusable setup or concepts that may be needed by several units belong in the repository-level [docs](./docs/).

## Shared docs

- [Ollama on WSL/Linux](./docs/ollama.md) — install Ollama, start its local API server, pull models (chat and decision models), and verify the service.

## Learning units

| Unit | Topic | Goal |
|---|---|---|
| [01](./01-mcp-local-llm/) | MCP + local LLM tool calling | Build an MCP server and let a small local LLM discover and call its tools |
| [02](./02-decision-models/) | Decision models | Ask a local decision model typed questions about a state, read its probabilities, and let application code act |

## Conventions

- Folders are ordered with a two-digit prefix: `01-`, `02-`, ...
- Prefer small examples over production scaffolding.
- Keep each unit independently runnable.
- Put Python source files under `src/` (or a domain-equivalent source directory when that is more natural).
- Put reusable environment/setup knowledge in root `docs/`.
- Put unit-specific concepts in that unit's `docs/`.
- Document the mental model before adding abstractions.
- First make the protocol flow visible; only then add frameworks.
