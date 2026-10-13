# EXE00 — Chunk RAG against a graph

Solved. One question, three pipelines, the same generator (`qwen3:1.7b`):

```text
chunks  BM25 (20 candidates) -> MiniLM -> top 3 chunks (notes and data models) -> generator
gold    rule planner -> start nodes -> follow the gold graph -> facts          -> generator
built   the same, on the parsed tree + the links extracted from the notes
```

## Run, one step at a time

### 1. Without a model

```bash
uv run python exercises/exe00-demo/exe00.py --inspect
```

320 tree nodes, 50 prose chunks, 123 gold links, 40 dev questions.

### 2. One question

```bash
uv run python exercises/exe00-demo/exe00.py --case 12
```

"Which mission is confirmed by the first rover's status result?" The first
run extracts the links of all 50 chunks (about 4 s per chunk on a CPU,
cached). Then, for each pipeline:

- **chunks:** the context panel shows three chunks; the answer depends on
  whether the one chunk with the mission is among them.
- **gold:** the plan panel shows the path `contains -> exposes_variable ->
  confirms` and the start `first rover -> rover1`; the context is the few
  facts on that path, as sentences.
- **built:** the same plan, on the built graph. If the extraction did not
  keep the `confirms` link, the path ends early, the context is empty, and
  the generator refuses.

### 3. The dev set

```bash
uv run python exercises/exe00-demo/exe00.py --eval
```

Measured (right answers):

| type        | questions | chunks | gold graph | built graph |
|-------------|-----------|--------|------------|-------------|
| single      | 8         | 3      | 6          | 6           |
| multi-hop   | 12        | 5      | 6          | 0           |
| aggregation | 10        | 2      | 6          | 4           |
| alias       | 6         | 3      | 5          | 3           |
| no-answer   | 4         | 4      | 4          | 4           |
| total       | 40        | 17     | 27         | 17          |

- **gold against chunks:** the graph wins on aggregation (6 against 2) and
  multi-hop (6 against 5): the answer is spread over several chunks, and
  top 3 holds some of them.
- **built against gold:** 0 multi-hop right. A multi-hop path needs every
  link on it; the built graph keeps about half of the links (EXE03), so a
  path of two or three links almost always breaks.
- **gold is not 40/40:** the query finds the right nodes for 34 questions
  (EXE05), and the small generator still refuses or rewrites some of them.
  EXE07 labels each failure.

`--pipeline gold` (or `chunks`, `built`) runs one pipeline only.
