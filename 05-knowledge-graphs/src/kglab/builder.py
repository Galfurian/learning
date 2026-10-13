"""Build the graph: the parsed tree, plus the links extracted from the prose.

For each chunk: extract mentions (extract.py), resolve each mention to a node
of the type the relation expects, keep the triple only if both ends resolve.
What does not resolve is counted, not guessed: a guessed node is a wrong edge
that looks right.

Resolution here has one more level than resolve.Resolver: "scoped". A
mention such as "the Busy flag" names a variable that many devices have; the
devices named in the mention, or else in the chunk, choose among them.
"""

import re
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from .corpus import Chunk
from .extract import Extraction, Mention
from .graph import Graph, Node
from .metrics import AMBIGUOUS
from .resolve import Resolution, Resolver, normalize
from .scenario import SCENARIO


def expected_types(relation: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    r = SCENARIO.relations[relation]
    return r.subject, r.object


OWNER = re.compile(SCENARIO.owner_pattern)


def owner(node_id: str) -> str:
    """The node that owns this one, by the scenario's id pattern: "alarm:assembly/EmergencyStop" -> "assembly"."""
    m = OWNER.match(node_id)
    return m.group(1) if m else node_id


def contains_words(text: str, phrase: str) -> bool:
    return bool(phrase) and re.search(rf"(?<![a-z0-9]){re.escape(phrase)}(?![a-z0-9])", text) is not None


class Linker:
    """Resolve mentions against a catalog: the tree nodes and the glossary nodes."""

    def __init__(self, catalog: Graph, *, ambiguous: dict[str, list[str]] | None = None) -> None:
        self.catalog = catalog
        self.ambiguous = ambiguous or {}
        self.by_type: dict[tuple[str, ...], Resolver] = {}
        self.devices = Resolver(catalog, types=("Device",), ambiguous=self.ambiguous)

    def _resolver(self, types: tuple[str, ...]) -> Resolver:
        if types not in self.by_type:
            self.by_type[types] = Resolver(self.catalog, types=types, ambiguous=self.ambiguous)
        return self.by_type[types]

    def devices_in(self, text: str) -> set[str]:
        """The devices a text names, by name or alias (ambiguous aliases name none)."""
        norm = normalize(text)
        found = set()
        for phrase, nodes in self.devices.normal.items():
            if len(nodes) == 1 and contains_words(norm, phrase):
                found |= nodes
        return found

    def resolve(self, mention: str, types: tuple[str, ...], chunk_text: str = "") -> Resolution:
        first = self._resolver(types).resolve(mention)
        if first.level in ("exact", "normalized"):
            return first
        if first.level == "ambiguous":
            names = [self.catalog.nodes[c] for c in first.candidates]
        else:
            # Node names that occur inside the mention: "the Busy flag of R-2" -> Busy.
            norm = normalize(mention)
            names = [n for n in self.catalog.nodes.values()
                     if n.type in types and any(contains_words(norm, normalize(x)) for x in [n.name, *n.aliases] if x)]
        if not names and norm in {t.lower() for t in types}:
            # A bare type word ("the incident", "the alarm") means the one node of that type the chunk names.
            names = [n for n in self.catalog.nodes.values() if n.type in types and any(
                contains_words(normalize(chunk_text), normalize(x)) for x in [n.name, *n.aliases] if x)]
            if len(names) == 1:
                return Resolution(mention, names[0].id, "chunk")
            names = []
        if not names:
            return Resolution(mention, None, "none")
        if len(names) == 1:
            return Resolution(mention, names[0].id, "scoped")
        # Many candidates: the devices named in the mention, or else in the chunk, choose.
        for scope in (self.devices_in(mention), self.devices_in(chunk_text)):
            narrowed = [n for n in names if owner(n.id) in scope]
            if len(narrowed) == 1:
                return Resolution(mention, narrowed[0].id, "scoped")
            if narrowed:
                names = narrowed
        return Resolution(mention, AMBIGUOUS, "ambiguous", tuple(sorted(n.id for n in names)))


@dataclass
class BuildReport:
    mentions: int = 0
    kept: int = 0
    invalid: int = 0                      # out of schema or not parseable (extract.py)
    reversed: int = 0                     # kept after swapping subject and object
    unresolved: Counter = field(default_factory=Counter)   # by level: none, ambiguous
    levels: Counter = field(default_factory=Counter)       # resolution level of each kept end
    dropped: list[tuple[str, Mention, str]] = field(default_factory=list)  # chunk id, mention, why


def add_links(graph: Graph, linker: Linker, chunk: Chunk, extraction: Extraction, report: BuildReport) -> None:
    report.invalid += len(extraction.invalid)
    for m in extraction.triples:
        report.mentions += 1
        s_types, o_types = expected_types(m.relation)
        s = linker.resolve(m.subject, s_types, chunk.text)
        o = linker.resolve(m.object, o_types, chunk.text)
        bad = [r for r in (s, o) if r.node in (None, AMBIGUOUS)]
        if bad:
            # Small models often write the triple backwards ("R-1 incident_on the incident").
            # If the ends fit the relation's types the other way round, the schema repairs the direction.
            s2 = linker.resolve(m.object, s_types, chunk.text)
            o2 = linker.resolve(m.subject, o_types, chunk.text)
            if all(r.node not in (None, AMBIGUOUS) for r in (s2, o2)):
                s, o, bad = s2, o2, []
                report.reversed += 1
        if bad:
            for r in bad:
                report.unresolved[r.level] += 1
            report.dropped.append((chunk.id, m, ", ".join(f"{r.mention!r}: {r.level}" for r in bad)))
            continue
        report.levels[s.level] += 1
        report.levels[o.level] += 1
        if graph.add_triple(s.node, m.relation, o.node, chunk.id):
            report.kept += 1


def catalog_from(tree: Graph, glossary: Iterable[Node]) -> Graph:
    """The nodes a mention may resolve to: the parsed tree and a glossary. No link edges."""
    catalog = Graph()
    for node in tree.nodes.values():
        catalog.add_node(node)
    for node in glossary:
        catalog.add_node(node)
    return catalog


def build(tree: Graph, glossary: Sequence[Node], chunks: Sequence[Chunk], extractions: dict[str, Extraction], *,
          ambiguous: dict[str, list[str]] | None = None) -> tuple[Graph, BuildReport]:
    """The built graph: a copy of the tree, plus every link whose two ends resolve."""
    graph = Graph()
    for node in [*tree.nodes.values(), *glossary]:
        graph.add_node(node)
    for e in tree.edges:
        graph.add_triple(e.s, e.r, e.o, e.source)
    linker = Linker(catalog_from(tree, glossary), ambiguous=ambiguous)
    report = BuildReport()
    for chunk in chunks:
        if chunk.id in extractions:
            add_links(graph, linker, chunk, extractions[chunk.id], report)
    return graph, report
