# EXE08 — The benchmark on the holdout

Solved. The three pipelines of EXE00 on the **holdout**: 20 questions
written and committed before the first benchmark run, never used to choose
a rule, a prompt or a model.

```bash
uv run python exercises/exe08-benchmark/exe08.py
```

Every choice was made on the dev set: the extraction prompt and its
example, the resolution rules, the 27 planner rules, the generator.

## Results

Measured (right answers, `qwen3:1.7b` for extraction and generation):

| type        | questions | chunks | gold graph | built graph |
|-------------|-----------|--------|------------|-------------|
| single      | 5         | 2      | 2          | 2           |
| multi-hop   | 5         | 0      | 0          | 0           |
| aggregation | 6         | 3      | 1          | 1           |
| alias       | 2         | 2      | 0          | 0           |
| no-answer   | 2         | 2      | 2          | 2           |
| total       | 20        | 9      | 5          | 5           |

On dev the gold graph won (27 against 17). On the holdout it loses (5
against 9). The graph did not change; the questions did.

## Why: the planner

Plans scored on the gold graph, without the generator:

| planner | dev: path right | holdout: path right | holdout: first failing stage |
|---------|-----------------|---------------------|------------------------------|
| rules   | 37/40           | 4/20                | PLAN 16 · NONE 4             |
| LLM     | 12/40           | 7/20                | PLAN 11 · LINKING 3 · NONE 6 |

The 27 rules match the wording of the dev questions. The holdout asks the
same kinds of questions with other words, and 16 of 20 get no plan or a
wrong one. The LLM planner is weaker on dev and loses less on the holdout:
it reads meaning, badly, where the rules read wording, exactly.

On the built graph the labels are EXTRACTION 2 · RESOLUTION 4 · PLAN 10 ·
NONE 4: when a plan is right, extraction and resolution still break half of
the paths.

## What this says

- A graph pipeline has more stages than chunk RAG, and each one has its own
  ceiling. Chunk RAG needs no plan: it degrades, it does not fall to zero.
- Rules tuned on 40 questions are a measurement of those 40 questions. The
  dev numbers of EXE05 were real, and they did not transfer.
- The gold graph is still a ceiling only for questions the planner
  understands. Improve the planner before the graph.
