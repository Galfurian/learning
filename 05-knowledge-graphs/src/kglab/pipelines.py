"""One question through a graph pipeline, or through chunk RAG, with every stage kept for diagnosis.

```text
graph:  QUESTION -> plan (start mentions, path) -> link mentions to nodes -> follow -> facts -> generator
chunks: QUESTION -> BM25 or embedding -> MiniLM -> top k chunks                      -> generator
```

The graph pipelines differ only in the graph: gold (B) or built from the
data models and the extracted links (C).
"""

from collections.abc import Sequence
from dataclasses import dataclass, field

from .builder import Linker
from .client import DEFAULT_CHAT_MODEL, Tracer, chat
from .corpus import Chunk
from .evalset import Question
from .generation import (AnswerScore, CitationReport, Context, build_messages, check_citations, chunk_context,
                         facts_context, score_answer)
from .graph import Edge, Graph, follow, follow_edges
from .metrics import AMBIGUOUS
from .planner import Plan
from .resolve import Resolution

ALL_TYPES = ("Line", "Cell", "Device", "Folder", "Variable", "Method", "Parameter", "Alarm", "Condition",
             "Bay", "Pallet", "Item", "Mission", "Incident")


@dataclass
class Answer:
    text: str = ""
    citations: CitationReport | None = None
    score: AnswerScore | None = None
    seconds: float = 0.0


@dataclass
class GraphRun:
    question: Question
    plan: Plan | None
    starts: list[Resolution] = field(default_factory=list)
    nodes: list[str] = field(default_factory=list)       # what the query returns
    edges: list[Edge] = field(default_factory=list)
    context: Context | None = None
    answer: Answer = field(default_factory=Answer)

    @property
    def start_ids(self) -> list[str]:
        return [r.node for r in self.starts if r.node not in (None, AMBIGUOUS)]


def link_starts(plan: Plan, linker: Linker, question: str) -> list[Resolution]:
    return [linker.resolve(m, ALL_TYPES, question) for m in plan.start]


def query(graph: Graph, plan: Plan | None, starts: Sequence[str]) -> tuple[list[str], list[Edge]]:
    if plan is None or not starts:
        return [], []
    return follow(graph, starts, plan.path), follow_edges(graph, starts, plan.path)


def generate(question: Question, context: Context, graph: Graph, *, model: str = DEFAULT_CHAT_MODEL,
             think: bool = False, tracer: Tracer | None = None) -> Answer:
    result = chat(model, build_messages(question.question, context), think=think, tracer=tracer)
    return Answer(result.content, check_citations(result.content, context.ids),
                  score_answer(result.content, question, graph), result.seconds)


def run_graph(question: Question, graph: Graph, linker: Linker, planner, *, generator: bool = True,
              model: str = DEFAULT_CHAT_MODEL, tracer: Tracer | None = None) -> GraphRun:
    """`planner` has .plan(text) -> Plan | None. `graph` answers; `linker` knows the names (catalog)."""
    plan = planner.plan(question.question)
    run = GraphRun(question, plan)
    if plan is not None:
        run.starts = link_starts(plan, linker, question.question)
        run.nodes, run.edges = query(graph, plan, run.start_ids)
    run.context = facts_context(graph, run.edges)
    if generator:
        run.answer = generate(question, run.context, graph, model=model, tracer=tracer)
    return run


@dataclass
class ChunkRun:
    question: Question
    chunks: list[Chunk]
    context: Context
    answer: Answer = field(default_factory=Answer)


def run_chunks(question: Question, chunks: Sequence[Chunk], graph: Graph, *, generator: bool = True,
               model: str = DEFAULT_CHAT_MODEL, tracer: Tracer | None = None) -> ChunkRun:
    """`chunks`: the retrieved top k, already reranked. `graph` only names the nodes for scoring."""
    context = chunk_context(chunks)
    run = ChunkRun(question, list(chunks), context)
    if generator:
        run.answer = generate(question, context, graph, model=model, tracer=tracer)
    return run
