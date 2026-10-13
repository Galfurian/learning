"""Entity resolution: a mention in the text -> one node of the graph, or none.

Two levels, measured apart:

- exact: the mention is a node id or a node name, as written;
- normalized: lowercase, no punctuation, no leading "the"; names and aliases.

A mention that fits two nodes is ambiguous: the resolver says so and does
not pick one. Picking one would merge two devices into one.
"""

import re
from collections import defaultdict
from dataclasses import dataclass

from .graph import Graph
from .metrics import AMBIGUOUS


def normalize(text: str) -> str:
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", text.strip())  # "NoAirPressure" -> "No Air Pressure"
    text = text.lower()
    text = re.sub(r"[^a-z0-9:/ -]+", " ", text)
    text = re.sub(r"[\s-]+", " ", text).strip()
    return re.sub(r"^the ", "", text)


@dataclass(frozen=True)
class Resolution:
    mention: str
    node: str | None          # a node id, AMBIGUOUS, or None
    level: str                # "exact", "normalized", "ambiguous", "none"
    candidates: tuple[str, ...] = ()


class Resolver:
    def __init__(self, graph: Graph, *, ambiguous: dict[str, list[str]] | None = None,
                 types: tuple[str, ...] | None = None) -> None:
        """Index the names and aliases of the nodes (only of `types`, if given)."""
        self.exact: dict[str, set[str]] = defaultdict(set)
        self.normal: dict[str, set[str]] = defaultdict(set)
        for node in graph.nodes.values():
            if types and node.type not in types:
                continue
            self.exact[node.id].add(node.id)
            if node.name:
                self.exact[node.name].add(node.id)
            for name in [node.id, node.name, *node.aliases]:
                if name:
                    self.normal[normalize(name)].add(node.id)
        for mention, nodes in (ambiguous or {}).items():
            self.normal[normalize(mention)].update(nodes)

    def resolve(self, mention: str) -> Resolution:
        hits = self.exact.get(mention.strip(), set())
        if len(hits) == 1:
            return Resolution(mention, next(iter(hits)), "exact")
        hits = hits or self.normal.get(normalize(mention), set())
        if len(hits) == 1:
            return Resolution(mention, next(iter(hits)), "normalized")
        if len(hits) > 1:
            return Resolution(mention, AMBIGUOUS, "ambiguous", tuple(sorted(hits)))
        return Resolution(mention, None, "none")
