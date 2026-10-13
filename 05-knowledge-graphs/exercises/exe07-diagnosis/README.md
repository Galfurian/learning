# EXE07 — The first failing stage

**Concept:** a wrong answer from the built graph can come from any stage.
Label each question with the first stage that failed:

```text
EXTRACTION -> RESOLUTION -> PLAN -> LINKING -> GENERATION -> NONE
```

- **EXTRACTION:** a gold edge on the question's path is missing, and the
  model wrote no mention with that relation in the edge's chunk;
- **RESOLUTION:** the edge is missing, but its chunk had such a mention,
  dropped because an end did not resolve;
- **PLAN:** no plan, or another path;
- **LINKING:** the plan's start mentions did not resolve to the gold starts;
- **GENERATION:** the graph returned the right nodes, the answer is wrong;
- **NONE:** right.

An operational label, not a causal proof: the first failure hides the later
ones.

## Task

Implement `diagnose(row)` in `exe07.py`. A row holds what the pipeline did
for one question (plan, starts, nodes, missing gold edges, dropped
mentions, answer check).

```bash
uv run python exercises/exe07-diagnosis/check.py
```

## Run

```bash
uv run python exercises/exe07-diagnosis/exe07.py
```

The first run builds the graph (cached extraction), runs the 40 dev
questions with the generator, and saves the rows in `.cache/rows/`. Later
runs only label.

Measured (built graph, `qwen3:1.7b` for extraction and generation):

| stage      | questions |
|------------|-----------|
| EXTRACTION | 4         |
| RESOLUTION | 13        |
| PLAN       | 1         |
| LINKING    | 2         |
| GENERATION | 4         |
| NONE       | 16        |

- **RESOLUTION is the largest stage:** the model wrote the fact, and the
  mention did not become a node. Eight of the twelve multi-hop questions stop
  here.
- **EXTRACTION:** d18, d19, d32, d33 are incident questions: the model
  never wrote `raised` or `incident_on` for those incidents.
- **GENERATION:** the graph was right and the answer was not (d10, d22: the
  route facts were there).

The order matters: improve resolution first (EXE04), then extraction.
