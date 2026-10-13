# EXE06 — Facts as context

**Concept:** the graph returns nodes and the edges on the path to them. The
generator reads text. Each edge becomes one numbered sentence, written with
its relation's phrase from `data/scenario.json`:

```text
[f1] on the route, Bay 1 is followed by Bay 2
[f2] on the route, Bay 2 is followed by Bay 3
```

Owned nodes carry their owner ("Busy of Rover R-1"); ids stay out of the
text. The fact id is what the answer cites; the source of the edge (a chunk
id or a data model path) stays with the app.

The first version gave the raw triples (`Bay 1 (bay:1) next_step Bay 2
(bay:2)`): `qwen3:1.7b` refused on clear facts, or copied the lines as the
answer.

## Task

Implement `facts_context(graph, edges, budget)` in `exe06.py`.

```bash
uv run python exercises/exe06-facts/check.py
```

## Run

```bash
uv run python exercises/exe06-facts/exe06.py
```

The three pipelines of EXE00, with your context builder in the graph ones.
Measured with the reference solution (right answers):

| type        | questions | chunks | gold graph | built graph |
|-------------|-----------|--------|------------|-------------|
| single      | 8         | 2      | 6          | 6           |
| multi-hop   | 12        | 5      | 6          | 0           |
| aggregation | 10        | 2      | 6          | 5           |
| alias       | 6         | 4      | 5          | 3           |
| no-answer   | 4         | 4      | 4          | 4           |

Citations valid: chunks 20/40, gold 31/40, built 36/40.

- The table differs by one or two answers from EXE00's run: the generator
  samples. Differences of one answer per type are noise.
- **Citations:** with facts, the generator cites `[f2]` far more reliably
  than `[rovers-missions]` with chunks. The built graph has the most valid
  citations because it refuses most: a refusal with no citation is valid.
- `--case N` prints the three contexts and answers of one question.
