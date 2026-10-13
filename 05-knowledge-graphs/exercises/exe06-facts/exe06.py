"""EXE06 — build a facts context. Task: see README.md in this folder."""

from collections.abc import Sequence

from kglab.generation import Context
from kglab.graph import Edge, Graph
from kglab.runners import run_facts


# TODO: turn graph edges into a compact Context for the answer generator.
# - write one numbered line per unique (subject, relation, object): [f1] ...;
# - write each fact with kglab.generation.fact_line(graph, edge): a sentence from the scenario's phrase;
# - keep sources as {fact_id: edge.source};
# - stop when the estimated token budget would be exceeded and count dropped edges;
# - return a kglab.generation.Context.
def facts_context(graph: Graph, edges: Sequence[Edge], budget: int = 1500) -> Context:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_facts(facts_context, __file__)
