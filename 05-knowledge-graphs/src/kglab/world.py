"""Everything an exercise loads for the current scenario: the gold graph, the parsed tree, the notes, the built graph, the questions.

The built graph needs one extraction per chunk. Extractions are cached; the
first run on a CPU takes minutes (about 7 s per chunk with qwen3:1.7b).
"""

import json
from collections.abc import Callable
from dataclasses import dataclass
from functools import cached_property

from .builder import BuildReport, Linker, build
from .client import DEFAULT_CHAT_MODEL, Tracer
from .corpus import GOLD_GRAPH, Chunk, load_notes
from .extract import Extraction, extract
from .graph import Graph, Node, load
from .parse import load_models
from .scenario import SCENARIO
from .scorecache import ScoreCache


@dataclass
class World:
    extract_model: str = DEFAULT_CHAT_MODEL

    @cached_property
    def gold(self) -> Graph:
        return load(GOLD_GRAPH)

    @cached_property
    def ambiguous(self) -> dict[str, list[str]]:
        return json.loads(GOLD_GRAPH.read_text(encoding="utf-8")).get("ambiguous", {})

    @cached_property
    def tree(self) -> Graph:
        return load_models()

    @cached_property
    def glossary(self) -> list[Node]:
        """The named entities that are not in the data models: bays, items, conditions, incidents, ...
        Their names and aliases are given (as a glossary or an ontology would give them); their edges are not."""
        return [n for n in self.gold.nodes.values() if n.type in SCENARIO.glossary_types]

    @cached_property
    def notes(self) -> list[Chunk]:
        return load_notes()

    @cached_property
    def gold_linker(self) -> Linker:
        return Linker(self.gold, ambiguous=self.ambiguous)

    def extractions(self, *, progress: Callable[[int, int, Chunk, Extraction], None] | None = None,
                    tracer: Tracer | None = None) -> dict[str, Extraction]:
        cache, out = ScoreCache(), {}
        for i, chunk in enumerate(self.notes, start=1):
            out[chunk.id] = extract(chunk.title, chunk.text, model=self.extract_model, cache=cache, tracer=tracer)
            if progress:
                progress(i, len(self.notes), chunk, out[chunk.id])
        return out

    def built(self, extractions: dict[str, Extraction]) -> tuple[Graph, BuildReport, Linker]:
        graph, report = build(self.tree, self.glossary, self.notes, extractions, ambiguous=self.ambiguous)
        return graph, report, Linker(graph, ambiguous=self.ambiguous)
