# learning

Repository of small, self-contained learning units.

The rule is simple: one topic = one folder = one runnable workspace.

## Layout

```text
learning/
├── README.md
├── .gitignore
└── NN-topic-name/
    ├── README.md
    ├── pyproject.toml
    ├── docs/
    ├── exercises/
    └── runnable source files
```

Each unit should contain:

- **README.md** — learning path, commands, and expected results.
- **workspace** — the smallest runnable project that demonstrates the topic.
- **docs/** — concepts worth keeping after the experiment.
- **exercises/** — small changes to make without copying a solution blindly.

## Learning units

| Unit | Topic | Goal |
|---|---|---|
| [01](./01-mcp-local-llm/) | MCP + local LLM tool calling | Build an MCP server and let a small local LLM discover and call its tools |

## Conventions

- Folders are ordered with a two-digit prefix: `01-`, `02-`, ...
- Prefer small examples over production scaffolding.
- Keep each unit independently runnable.
- Document the mental model before adding abstractions.
- First make the protocol flow visible; only then add frameworks.
