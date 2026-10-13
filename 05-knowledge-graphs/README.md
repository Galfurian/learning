# 05 — Knowledge graphs

Goal: turn documents into typed facts, connect them in a graph, and answer
questions by following the connections. Measure what the graph adds over
chunk retrieval, and what it loses on the way.

The central rule of this unit: **a graph can only connect the facts that its
extraction kept.**

No graph database, no framework. The graph is two dicts; a query is a loop
over relations; the extraction is one JSON request per chunk.

## The scenario

An invented production line: eight devices around a pallet conveyor loop (a
conveyor, a vertical warehouse, two mobile robots, a board tester, an
engraving cell, an assembly cell, a camera quality cell). Its shape follows a
real lab line: every device has an OPC-UA-like data model (folders,
variables, methods, alarm flags), and the documents around it are prose
(operation notes, a line note, an incident log).

The data models give a **tree** (what each device contains). They never say
which bay a robot serves, which alarm stops which cell, or which incident
happened where: those **links** are only in the prose.

Everything that is specific to the line is in `data/scenario.json`: node
types, relations (tree or link), the data model format, the prompt texts,
the planner rules, the paths. The code in `src/kglab/` reads the scenario;
another domain is another JSON file (`KGLAB_SCENARIO=path/to/scenario.json`).

## What you will build

```text
data/line/models/*.yml ── PARSE (no model) ─────────────┐  tree: contains, exposes_*, has_parameter, returns, has_alarm
                                                        ├─ GRAPH: nodes, typed edges, a source per edge
data/line/notes/*.md ──── EXTRACT (LLM, JSON schema) ──┐│
                          RESOLVE mentions -> nodes ───┴┘  links: serves_bay, moves, stops, requires, raised, ...

QUESTION -> PLAN (start mentions + relation path) -> LINK mentions -> FOLLOW the graph -> FACTS -> GENERATOR
```

Three pipelines answer the same questions:

| pipeline | context for the generator |
|----------|---------------------------|
| chunks   | BM25 + MiniLM (unit 04), top 3 chunks of notes and data models |
| gold     | facts from the gold graph: the ceiling of the graph approach |
| built    | facts from the graph built here: the parsed tree + the extracted links |

## Prerequisites

Inside WSL:

- Python 3.11+ and `uv`
- Ollama 0.35 or later, with `qwen3:1.7b` (extraction, planning option,
  generation)
- the MiniLM cross-encoder downloads from Hugging Face on first use (about
  90 MB), as in unit 04

## 0. Clone and install

```bash
git clone git@github.com:Galfurian/learning.git
cd learning/05-knowledge-graphs
uv sync
ollama pull qwen3:1.7b
```

`OLLAMA_HOST` chooses the Ollama server, as in unit 04 (`export
OLLAMA_HOST=<host>:11434`). The unit is designed for a CPU-only machine.

## 1. First without a model

```bash
uv run pytest
uv run python exercises/exe00-demo/exe00.py --inspect
```

## 2. Let the models run

```bash
uv run python exercises/exe00-demo/exe00.py --case 12
```

The first run extracts the links of all 50 note chunks (about 4 s per chunk
with `qwen3:1.7b` on a CPU, cached in `.cache/`). Then the question goes
through the three pipelines, and each prints its context and its answer.

### All options

| Option                  | Effect |
|-------------------------|--------|
| `--inspect`             | show the setup without calling a model |
| `--verbose`             | show every HTTP request and response |
| `--question "..."`      | ask this question instead of the dev set |
| `--case N`              | run only question N of the dev set |
| `--eval`                | run the whole set and print the tables |
| `--pipeline P`          | `all` (default), `chunks`, `gold`, `built` (EXE00) |
| `--model M`             | generator |
| `--extract-model M`     | model that extracts the links |

## 3. Read the code in this order

1. `data/scenario.json`, then `src/kglab/scenario.py`.
2. `src/kglab/graph.py`: nodes, edges, `follow`.
3. `src/kglab/parse.py`: the data model as a tree.
4. `src/kglab/extract.py`: the prompt, the JSON schema, the parser.
5. `src/kglab/resolve.py` and `src/kglab/builder.py`: mentions to nodes.
6. `src/kglab/planner.py`: the query DSL, rules and LLM.
7. `src/kglab/pipelines.py`, `generation.py`: facts as context.
8. `src/kglab/benchmark.py`: the first failing stage.
9. `docs/mental-model.md`.

`client`, `ui`, `bm25`, `embedders`, `index`, `rerankers`, `cache`,
`scorecache` are copies from unit 04, trimmed; each says so in its first line.

## 4. Write your own pieces

Continue with [exercises/README.md](exercises/README.md).

## Files

```text
05-knowledge-graphs/
├── README.md
├── pyproject.toml
├── data/
│   ├── scenario.json       # everything specific to the line
│   ├── build.py            # writes the line, the gold graph and the mentions (deterministic)
│   ├── line/models/*.yml   # 8 data models (tree)
│   ├── line/notes/*.md     # 50 prose chunks (links)
│   ├── gold.json           # the gold graph: 366 nodes, 123 links
│   ├── mentions.json       # surface forms of the entities, for EXE04
│   ├── dev.json            # 40 dev questions
│   └── holdout.json        # 20 holdout questions
├── docs/mental-model.md
├── scripts/measure_extraction.py
├── src/kglab/
├── tests/
└── exercises/
```

## The key lesson

A graph can only connect the facts that its extraction kept. The data models
give the tree for free; the links between devices are in the prose, and each
one passes extraction, then resolution, before a query can follow it.
Measure each stage apart.
