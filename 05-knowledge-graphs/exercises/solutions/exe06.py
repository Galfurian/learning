"""EXE06 — build a facts context. Task: see README.md in this folder."""

from collections.abc import Sequence

from kglab.generation import Context, estimate_tokens, fact_line
from kglab.graph import Edge, Graph
from kglab.runners import run_facts


def facts_context(graph: Graph, edges: Sequence[Edge], budget: int = 1500) -> Context:
    ids, lines, sources, used, dropped = [], [], {}, 0, 0
    seen = set()
    for edge in edges:
        key = (edge.s, edge.r, edge.o)
        if key in seen:
            continue
        seen.add(key)
        fact_id = f"f{len(ids) + 1}"
        line = f"[{fact_id}] {fact_line(graph, edge)}"
        cost = estimate_tokens(line) + 1
        if used + cost > budget:
            dropped += 1
            continue
        ids.append(fact_id)
        lines.append(line)
        sources[fact_id] = edge.source
        used += cost
    text = "\n".join(lines)
    return Context(ids, text, estimate_tokens(text), sources, dropped)


if __name__ == "__main__":
    run_facts(facts_context, __file__)
