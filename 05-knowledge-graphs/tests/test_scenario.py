import json
import subprocess
import sys
from pathlib import Path

import pytest

from kglab.scenario import SCENARIO, parse_scenario

OTHER = {
    "name": "library",
    "paths": {"models": "models", "notes": "notes", "gold": "gold.json", "manifest": "m.json",
              "dev": "dev.json", "holdout": "holdout.json"},
    "node_types": ["Library", "Room", "Shelf", "Section", "Book", "Service", "Field", "Notice", "Author"],
    "glossary_types": ["Author"],
    "owner_pattern": "^(?:notice:)?([^/:]+)",
    "owner_type": "Shelf",
    "relations": {
        "holds": {"kind": "tree", "subject": ["Library", "Room", "Shelf", "Section"],
                  "object": ["Room", "Shelf", "Section"], "meaning": "holds"},
        "lists": {"kind": "tree", "subject": ["Shelf", "Section"], "object": ["Book"], "meaning": "lists"},
        "offers": {"kind": "tree", "subject": ["Shelf", "Section"], "object": ["Service"], "meaning": "offers"},
        "needs": {"kind": "tree", "subject": ["Service"], "object": ["Field"], "meaning": "needs"},
        "gives": {"kind": "tree", "subject": ["Service"], "object": ["Book"], "meaning": "gives"},
        "posts": {"kind": "tree", "subject": ["Shelf"], "object": ["Notice"], "meaning": "posts"},
        "written_by": {"kind": "link", "subject": ["Book"], "object": ["Author"], "meaning": "the author wrote it"},
    },
    "data_model": {"format": "opcua-yaml", "root": "library:main", "root_type": "Library", "root_name": "the library",
                   "cell_prefix": "room:", "alarm_folder": "Notices", "alarm_prefix": "notice:",
                   "types": {"device": "Shelf", "cell": "Room", "folder": "Section", "variable": "Book",
                             "method": "Service", "parameter": "Field", "alarm": "Notice"},
                   "relations": {"contains": "holds", "exposes_variable": "lists", "exposes_method": "offers",
                                 "has_parameter": "needs", "returns": "gives", "has_alarm": "posts"}},
    "extraction": {"documents": "the catalog notes of a library"},
    "generation": {"domain": "a library", "documents_label": "Catalog notes", "refusal": "Not in the catalog."},
}


def test_default_scenario_is_consistent():
    assert set(SCENARIO.glossary_types) <= set(SCENARIO.node_types)
    assert SCENARIO.kind("tree") and SCENARIO.kind("link")
    assert SCENARIO.path("gold").exists()


def test_unknown_type_is_rejected():
    bad = json.loads(json.dumps(OTHER))
    bad["relations"]["written_by"]["object"] = ["Person"]
    with pytest.raises(ValueError, match="unknown node types"):
        parse_scenario(bad, Path("."))


def test_another_scenario_changes_prompts_and_relations(tmp_path):
    (tmp_path / "scenario.json").write_text(json.dumps(OTHER))
    code = ("from kglab.extract import LINK_RELATIONS, system_prompt\n"
            "from kglab.generation import REFUSAL\n"
            "from kglab.planner import ALL_RELATIONS\n"
            "print(list(LINK_RELATIONS), ALL_RELATIONS, REFUSAL, system_prompt().splitlines()[0])")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True,
                         env={"KGLAB_SCENARIO": str(tmp_path / "scenario.json"), "PATH": ""}).stdout
    assert out.strip() == ("['written_by'] ('holds', 'lists', 'offers', 'needs', 'gives', 'posts', 'written_by') "
                           "Not in the catalog. You extract facts from the catalog notes of a library.")


SHELF = {"device": "shelf1", "name": "Shelf A", "cell": "north", "aliases": ["the first shelf"], "nodes": [
    {"folder": "Novels", "children": [{"variable": "Dune", "type": "string"}]},
    {"folder": "Notices", "children": [{"variable": "Closed", "type": "bool"}]},
    {"method": "Lend", "parameters": [{"name": "card"}], "returns": [{"name": "Receipt"}]},
]}
SHELF2 = {**SHELF, "device": "shelf2", "name": "Shelf B", "aliases": ["the second shelf"]}


def test_another_scenario_parses_and_links_with_its_own_names(tmp_path):
    import yaml
    (tmp_path / "models").mkdir()
    (tmp_path / "models" / "shelf1.yml").write_text(yaml.safe_dump(SHELF))
    (tmp_path / "models" / "shelf2.yml").write_text(yaml.safe_dump(SHELF2))
    (tmp_path / "scenario.json").write_text(json.dumps(OTHER))
    code = ("from kglab.parse import load_models\n"
            "from kglab.builder import Linker\n"
            "g = load_models()\n"
            "print(sorted({n.type for n in g.nodes.values()}))\n"
            "print(sorted(g.relations()))\n"
            "r = Linker(g).resolve('Dune', ('Book',), 'The first shelf is full.')\n"
            "print(r.node, r.level)")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True,
                         env={"KGLAB_SCENARIO": str(tmp_path / "scenario.json"), "PATH": ""}).stdout.splitlines()
    assert out[0] == "['Book', 'Field', 'Library', 'Notice', 'Room', 'Section', 'Service', 'Shelf']"
    assert out[1] == "['gives', 'holds', 'lists', 'needs', 'offers', 'posts']"
    assert out[2] == "shelf1/Novels/Dune scoped"
