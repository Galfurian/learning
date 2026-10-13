# EXE05 — From a question to a path

**Concept:** a graph answers only a query. A planner turns the question
into a plan in a small DSL:

```json
{"start": ["first rover"], "path": ["contains", "exposes_variable", "confirms"], "op": "list"}
```

`start` holds mentions (they are linked to nodes like extracted mentions),
`path` holds relations (`^` walks an edge backwards), `op` is `list` or
`count`. A wrong hop is a wrong answer, even when the graph is perfect.

Two planners:

- **rules:** a regex per question shape, written by reading the dev
  questions. Predictable, and blind to any wording its author did not
  foresee;
- **LLM:** `qwen3:1.7b` fills the same JSON, with the relations and three
  invented examples in the prompt (`planner_examples` in
  `data/scenario.json`).

## Task

Implement `plan(question)` in `exe05.py`: add rules to `RULES` until the dev
questions get their paths. The scaffold has three.

```bash
uv run python exercises/exe05-plan/check.py
```

## Run, one step at a time

### 1. Your rules

```bash
uv run python exercises/exe05-plan/exe05.py
```

Scored on the gold graph, so only the plan and the linking can fail. With
the three rules of the scaffold, most questions get no plan (PLAN). Measured
with the reference solution (27 rules): path right **37/40**, start right
**30/35**, answer recall **0.86** (PLAN 3, LINKING 2).

- The 3 PLAN failures are the questions with a long list of start nodes
  (d25, d26, d29): a rule with one `(?P<x>...)` group cannot take ten
  mentions.
- LINKING (d01, d02): "conveyor alarm reset" and "camera's inspection
  result flag" do not match a node name or alias.

### 2. Against the LLM planner

```bash
uv run python exercises/exe05-plan/exe05.py --llm
```

Measured: LLM **12/40** paths right, start right 15/35, answer recall 0.34.
Without the three examples in the prompt it was 2/40, with type words as
starts ("Device") and chains of unrelated relations. With the examples it
copies them: "Which condition does ExtractTray require?" became `requires ->
observed_by`, the shape of the third example. It also skips the tree hops:
"the first rover's status result" became one `observed_by` hop instead of
`contains -> exposes_variable -> confirms`.

The rules win here because they were written for these 40 questions. The
holdout (EXE08) asks new ones.
