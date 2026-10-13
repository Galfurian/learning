"""The graph: nodes, typed edges, and the source of every edge.

No graph database on purpose. A graph is two dicts: the nodes by id, and the
edges by (subject, relation). Following a relation is a dict lookup; a path
is a loop over relations.
"""

import json
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Edge:
    s: str          # subject node id
    r: str          # relation
    o: str          # object node id
    source: str     # chunk id or data model path that states the edge


@dataclass
class Node:
    id: str
    type: str
    name: str = ""
    aliases: list[str] = field(default_factory=list)
    props: dict[str, Any] = field(default_factory=dict)


class Graph:
    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}
        self.edges: list[Edge] = []
        self._out: dict[tuple[str, str], list[Edge]] = defaultdict(list)
        self._in: dict[tuple[str, str], list[Edge]] = defaultdict(list)
        self._seen: set[tuple[str, str, str]] = set()

    def add_node(self, node: Node) -> None:
        self.nodes.setdefault(node.id, node)

    def add_triple(self, s: str, r: str, o: str, source: str) -> bool:
        """Add one edge; False if the same (s, r, o) is already there."""
        if (s, r, o) in self._seen:
            return False
        self._seen.add((s, r, o))
        edge = Edge(s, r, o, source)
        self.edges.append(edge)
        self._out[s, r].append(edge)
        self._in[o, r].append(edge)
        return True

    def neighbors(self, node: str, relation: str, *, backward: bool = False) -> list[str]:
        """The nodes one `relation` edge away; backward follows o -> s."""
        if backward:
            return [e.s for e in self._in.get((node, relation), [])]
        return [e.o for e in self._out.get((node, relation), [])]

    def edges_on(self, node: str, relation: str, *, backward: bool = False) -> list[Edge]:
        index = self._in if backward else self._out
        return list(index.get((node, relation), []))

    def triples(self) -> set[tuple[str, str, str]]:
        return set(self._seen)

    def relations(self) -> set[str]:
        return {e.r for e in self.edges}


def step(relation: str) -> tuple[str, bool]:
    """'serves_bay' -> ('serves_bay', False); '^serves_bay' -> ('serves_bay', True)."""
    return (relation[1:], True) if relation.startswith("^") else (relation, False)


def follow(graph: Graph, start: Iterable[str], relations: Sequence[str]) -> list[str]:
    """Follow `relations` in order from the start nodes; the end nodes, sorted, no repeats.

    A relation that starts with '^' is followed backwards (object -> subject).
    """
    frontier = set(start)
    for relation in relations:
        name, backward = step(relation)
        frontier = {n for node in frontier for n in graph.neighbors(node, name, backward=backward)}
    return sorted(frontier)


def follow_edges(graph: Graph, start: Iterable[str], relations: Sequence[str]) -> list[Edge]:
    """The edges on the paths that `follow` walks and that reach an end node: the evidence of the answer.

    Branches that die on the way (a folder with no matching variable) are left out.
    """
    frontier, layers = set(start), []
    for relation in relations:
        name, backward = step(relation)
        layer = [e for node in sorted(frontier) for e in graph.edges_on(node, name, backward=backward)]
        layers.append((layer, backward))
        frontier = {e.s if backward else e.o for e in layer}
    keep, used = frontier, []
    for layer, backward in reversed(layers):
        kept = [e for e in layer if (e.s if backward else e.o) in keep]
        used = kept + used
        keep = {e.o if backward else e.s for e in kept}
    return used


def to_json(graph: Graph) -> dict[str, Any]:
    return {
        "nodes": [vars(n) for n in graph.nodes.values()],
        "edges": [vars(e) for e in graph.edges],
    }


def from_json(data: dict[str, Any]) -> Graph:
    graph = Graph()
    for n in data.get("nodes", []):
        graph.add_node(Node(n["id"], n["type"], n.get("name", ""), list(n.get("aliases", [])), dict(n.get("props", {}))))
    for e in data.get("edges", []):
        graph.add_triple(e["s"], e["r"], e["o"], e["source"])
    return graph


def save(graph: Graph, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(to_json(graph), indent=1, ensure_ascii=False) + "\n", encoding="utf-8")


def load(path: Path) -> Graph:
    return from_json(json.loads(path.read_text(encoding="utf-8")))
