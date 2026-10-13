"""The first failing stage of one question, for a graph pipeline.

```text
EXTRACTION -> RESOLUTION -> PLAN -> LINKING -> GENERATION -> NONE
```

- EXTRACTION: an edge on the gold path is not in the graph, and no extracted
  mention in its source chunk had that relation;
- RESOLUTION: the edge is missing, but its chunk had a mention with that
  relation that did not resolve (or resolved to other nodes);
- PLAN: no plan, or a plan with another relation path;
- LINKING: the plan's start mentions did not resolve to the gold start nodes;
- GENERATION: the graph returned the right nodes, the answer is still wrong;
- NONE: right answer.

An operational label, not a causal proof: the first stage that fails hides
the later ones.
"""

from collections.abc import Sequence

from .builder import BuildReport
from .evalset import Question
from .graph import Edge, Graph, follow_edges
from .metrics import path_correct
from .pipelines import GraphRun

STAGES = ("EXTRACTION", "RESOLUTION", "PLAN", "LINKING", "GENERATION", "NONE")


def missing_gold_edges(question: Question, gold: Graph, graph: Graph) -> list[Edge]:
    """The gold edges on the question's gold path that the graph does not have."""
    if question.gold_path is None:
        return []
    have = graph.triples()
    return [e for e in follow_edges(gold, question.gold_path.start, question.gold_path.relations)
            if (e.s, e.r, e.o) not in have]


def diagnose(run: GraphRun, gold: Graph, graph: Graph, report: BuildReport | None = None) -> str:
    q = run.question
    if not q.answerable:
        if run.nodes:
            return "PLAN"
        return "NONE" if (run.answer.score is None or run.answer.score.ok) else "GENERATION"
    missing = missing_gold_edges(q, gold, graph)
    if missing:
        dropped = {(cid, m.relation) for cid, m, _ in (report.dropped if report else [])}
        if any((e.source, e.r) in dropped for e in missing):
            return "RESOLUTION"
        return "EXTRACTION"
    if q.gold_path is None or run.plan is None or not path_correct(run.plan.path, q.gold_path.relations):
        return "PLAN"
    if set(run.start_ids) != set(q.gold_path.start):
        return "LINKING"
    if run.answer.score is not None and not run.answer.score.ok:
        return "GENERATION"
    return "NONE"


def count_stages(labels: Sequence[str]) -> dict[str, int]:
    return {s: sum(1 for x in labels if x == s) for s in STAGES}


def stages_text(labels: Sequence[str]) -> str:
    """"PLAN 3 · LINKING 3 · NONE 34": the stages that occur, in pipeline order."""
    return " · ".join(f"{s} {n}" for s, n in count_stages(labels).items() if n)
