"""The scenario: everything kglab knows about one domain, read from one JSON file.

The code knows graphs, mentions, plans and checks. The scenario says what the
nodes and relations are, which relations come from the data models (tree)
and which from the prose (link), how to read the data models, what the
prompts say, and where the files are. Another domain is another JSON file:

    KGLAB_SCENARIO=path/to/scenario.json uv run python ...

The scenario is chosen once per process, at import. Paths in the file are
relative to the file's folder.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .cache import UNIT_ROOT

DEFAULT_SCENARIO = UNIT_ROOT / "data" / "scenario.json"


@dataclass(frozen=True)
class Relation:
    name: str
    kind: str                       # "tree": parsed from the data models; "link": extracted from prose
    subject: tuple[str, ...]
    object: tuple[str, ...]
    meaning: str
    phrase: str = "{s} {relation} {o}"   # how a fact reads in the generator's context


@dataclass(frozen=True)
class Scenario:
    name: str
    folder: Path
    paths: dict[str, str]
    node_types: tuple[str, ...]
    glossary_types: tuple[str, ...]
    owner_pattern: str              # regex; group 1 of a node id is the id of the node that owns it
    owned_types: tuple[str, ...]    # types named with their owner in a fact: "Busy of Rover R-1"
    owner_type: str                 # the type that owns the others (a device): it scopes ambiguous names
    relations: dict[str, Relation]
    data_model: dict[str, Any]
    extraction: dict[str, Any]
    generation: dict[str, str]
    planner_rules: list[dict[str, Any]] = field(default_factory=list)
    planner_examples: list[dict[str, Any]] = field(default_factory=list)

    def path(self, key: str) -> Path:
        return self.folder / self.paths[key]

    def kind(self, kind: str) -> dict[str, Relation]:
        return {n: r for n, r in self.relations.items() if r.kind == kind}


def parse_scenario(data: dict[str, Any], folder: Path) -> Scenario:
    types = tuple(data["node_types"])
    relations = {}
    for name, r in data["relations"].items():
        rel = Relation(name, r["kind"], tuple(r["subject"]), tuple(r["object"]), r["meaning"],
                       r.get("phrase", "{s} {relation} {o}"))
        if rel.kind not in ("tree", "link"):
            raise ValueError(f"relation {name}: kind must be 'tree' or 'link', not {rel.kind!r}")
        unknown = [t for t in (*rel.subject, *rel.object) if t not in types]
        if unknown:
            raise ValueError(f"relation {name}: unknown node types {unknown}")
        relations[name] = rel
    unknown = [t for t in [*data.get("glossary_types", []), *data.get("owned_types", []),
                           *([data["owner_type"]] if "owner_type" in data else []),
                           *data["data_model"].get("types", {}).values()] if t not in types]
    if unknown:
        raise ValueError(f"unknown node types {unknown}")
    unknown = [r for r in data["data_model"].get("relations", {}).values() if r not in relations]
    if unknown:
        raise ValueError(f"data_model.relations: unknown relations {unknown}")
    return Scenario(
        name=data["name"], folder=folder, paths=dict(data["paths"]), node_types=types,
        glossary_types=tuple(data.get("glossary_types", [])), owner_pattern=data["owner_pattern"],
        owned_types=tuple(data.get("owned_types", [])), owner_type=data.get("owner_type", types[0]),
        relations=relations, data_model=dict(data["data_model"]), extraction=dict(data["extraction"]),
        generation=dict(data["generation"]), planner_rules=list(data.get("planner_rules", [])),
        planner_examples=list(data.get("planner_examples", [])),
    )


def load_scenario(path: Path | str | None = None) -> Scenario:
    path = Path(path or os.environ.get("KGLAB_SCENARIO") or DEFAULT_SCENARIO).resolve()
    return parse_scenario(json.loads(path.read_text(encoding="utf-8")), path.parent)


SCENARIO = load_scenario()
