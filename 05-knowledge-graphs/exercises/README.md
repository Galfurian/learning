# Exercises

Each exercise is one folder with three files:

```text
exeNN-topic/
├── README.md   # the task, the concept, and the runs with what to look at
├── exeNN.py    # the file you edit: one piece of the pipeline, with a TODO
└── check.py    # verifies your file with fake data, without any model
```

Start with `exe00-demo`: it is solved. Then do the others in order. Each
builds one piece by hand; later exercises use the library version in
`src/kglab/`, so a mistake in one does not break the next. `exe08-benchmark`
is solved again: the three pipelines on the holdout.

| #  | Folder                                    | You write                     | Concept |
|----|-------------------------------------------|-------------------------------|---------|
| 00 | [exe00-demo](exe00-demo/)                 | nothing                       | chunk RAG against a graph, on the same question |
| 01 | [exe01-tree](exe01-tree/)                 | `parse_model(data, file, graph)` | the data model gives the tree; no links between devices |
| 02 | [exe02-follow](exe02-follow/)             | `follow(graph, start, relations)` | a query is a relation path; the tree alone cannot answer |
| 03 | [exe03-extraction](exe03-extraction/)     | `parse_triples(raw)`          | LLM extraction with a JSON schema; precision and recall per relation |
| 04 | [exe04-resolution](exe04-resolution/)     | `normalize`, `resolve`        | mentions to nodes; exact, normalized, ambiguous |
| 05 | [exe05-plan](exe05-plan/)                 | `plan(question)`              | question to path; rules against an LLM |
| 06 | [exe06-facts](exe06-facts/)               | `facts_context(graph, edges)` | facts as context; graph against chunks per question type |
| 07 | [exe07-diagnosis](exe07-diagnosis/)       | `diagnose(row)`               | the first failing stage |
| 08 | [exe08-benchmark](exe08-benchmark/)       | nothing                       | the three pipelines on the holdout |

## Commands

Run from the unit folder (`05-knowledge-graphs/`):

```bash
uv run python exercises/exe02-follow/check.py                 # verify, no model
uv run python exercises/exe02-follow/exe02.py --inspect       # setup, no model
uv run python exercises/exe02-follow/exe02.py --case 9        # one dev question
uv run python exercises/exe02-follow/exe02.py                 # the whole dev set
```

`OLLAMA_HOST=host:port` sends every Ollama request to another machine (see
the unit README). Keep one local model loaded at a time.

## Solutions

Reference solutions are in [solutions/](solutions/). Try first. To check a
solution, pass its path to the check:

```bash
uv run python exercises/exe04-resolution/check.py exercises/solutions/exe04.py
```

## Extra

No scaffold. Measure on the dev set; report on the holdout only once.

1. **A hybrid context.** Give the generator the graph facts and the top 3
   chunks together. Which question types gain, which lose?
2. **The graph answers alone.** Return the query's node names without a
   generator. Compare with the generated answers: what does the generator
   add, and what does it lose?
3. **Another scenario.** Write a small `scenario.json` for another domain
   (two data models, five notes) and run EXE01–EXE03 with
   `KGLAB_SCENARIO=...`.
4. **The lab data model format.** Write a second parser for YAML files with
   OPC-UA node tags (`!!FolderNode`, `!!MethodNode`, ...) and select it with
   `data_model.format`.
