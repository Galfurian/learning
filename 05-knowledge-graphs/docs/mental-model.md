# Mental model: knowledge graphs

Numbers come from runs on the invented line of this unit (8 data models, 50
prose chunks, 123 gold links between devices) and its dev set (40
questions), with `qwen3:1.7b` on a CPU-only laptop.

## 1. A fact is a typed triple with a source

```text
(Rover R-1, serves_bay, Bay 5)      source: rovers-missions
(rover1/Status, exposes_variable, rover1/Status/Busy)   source: models/rover1.yml#Status/Busy
```

A graph is a set of such triples: two dicts, the nodes by id and the edges
by (subject, relation). The source of every edge is what makes a citation
possible and an error traceable.

## 2. Two kinds of edges, two ways to get them

- **Tree edges** come from the data models (`contains`, `exposes_variable`,
  `exposes_method`, `has_parameter`, `returns`, `has_alarm`). A parser reads
  them: 320 nodes, 319 edges, precision and recall 1.00, no model.
- **Link edges** connect devices (`serves_bay`, `moves`, `stops`,
  `requires`, `observed_by`, `confirms`, `next_step`, `incident_on`,
  `raised`, `fixed_by_method`). The data models have none of them: 0 of 123.
  They are only in the prose, and an LLM must extract them.

On the tree alone, 6 of the 35 dev gold paths return the right answer set;
on the gold graph, 35 of 35.

## 3. Extraction: from prose to mentions

One request per chunk. The JSON schema in Ollama's `format` field lists the
relations as an enum, so the model cannot invent a relation name. It can
still pick the wrong one, put the triple backwards, or keep a fact the text
denies ("R-2 does not serve bay 3"): the schema constrains the form, not the
truth.

The model writes **mentions** ("the first rover"), not node ids.

## 4. Resolution: from mentions to nodes

| resolver (349 mentions)                                 | accuracy |
|---------------------------------------------------------|----------|
| exact name or id                                        | 0.35     |
| + normalized names and aliases                          | 0.62     |
| + the relation's types and the devices the chunk names  | 0.92     |

"Busy flag" fits the Busy variable of every device: only the chunk tells
which. "The rover" fits two robots: the right answer is "ambiguous", not a
guess. A guess merges two entities, and the wrong edge looks right.

Small models also write triples backwards ("R-1 incident_on the incident");
the relation's types repair the direction.

## 5. What the built graph keeps

| model       | s per chunk (CPU) | link precision | link recall |
|-------------|-------------------|----------------|-------------|
| qwen3:1.7b  | 3.9               | 0.93           | 0.45        |
| qwen3:4b    | 13.0              | 0.96           | 0.40        |

High precision, low recall: what the graph has is mostly right, and half of
the links are missing. **A graph can only connect the facts that its
extraction kept.** A larger model did not help here; resolution lost more
than extraction.

## 6. Questions become paths

A plan is a small DSL: start mentions, a relation path (`^` walks an edge
backwards), and `list` or `count`.

```json
{"start": ["first rover"], "path": ["contains", "exposes_variable", "confirms"], "op": "list"}
```

Rules written by reading the dev questions plan 37 of 40 right. A rule
matches wording, not meaning: a new phrasing gets no plan. The LLM planner
reads any phrasing and can pick a wrong hop.

## 7. Facts as context

The facts on the path become numbered sentences, written with each
relation's phrase from the scenario:

```text
[f1] on the route, Bay 1 is followed by Bay 2
[f2] on the route, Bay 2 is followed by Bay 3
```

Raw triples with ids (`Bay 1 (bay:1) next_step Bay 2 (bay:2)`) confused
`qwen3:1.7b`: it refused or copied the lines.

## 8. The first failing stage

```text
EXTRACTION -> RESOLUTION -> PLAN -> LINKING -> GENERATION -> NONE
```

An operational label, as in unit 04: the first stage that fails hides the
later ones.

## 9. Dev against holdout

On the dev set the gold graph answered 27 of 40 and chunk RAG 17. On the
holdout (20 new questions) the gold graph answered 5 and chunk RAG 9. The
27 planner rules gave the right path for 37 of 40 dev questions and for 4
of 20 holdout questions; the LLM planner for 12 of 40 and 7 of 20. Rules
fitted on the dev wording did not transfer.

## 10. When not to use a graph

- One fact in one chunk: chunk RAG answers it, with no extraction cost.
- The schema is a decision: a question about a relation the schema does not
  have has no path.
- Every new document passes extraction and resolution again.

A graph database (Neo4j) or RDF with SPARQL adds storage, indexes and a
query language for millions of edges. Here the graph has a few hundred
edges, and a loop over dicts shows every step.

## 11. Toward context graphs (unit 06)

This graph says what is connected. It does not say who decided what, when,
and why: incidents have dates, and every edge has a source, but there are no
decisions, no versions, no time. A context graph adds those: the next unit
starts from this graph.
