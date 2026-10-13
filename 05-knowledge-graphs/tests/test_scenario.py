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
    "node_types": ["Shelf", "Book", "Author"],
    "glossary_types": ["Author"],
    "owner_pattern": "^([^/]+)",
    "relations": {
        "contains": {"kind": "tree", "subject": ["Shelf"], "object": ["Book"], "meaning": "the shelf holds the book"},
        "written_by": {"kind": "link", "subject": ["Book"], "object": ["Author"], "meaning": "the author wrote it"},
    },
    "data_model": {"format": "opcua-yaml", "root": "library:main", "root_type": "Shelf", "root_name": "the library",
                   "cell_prefix": "room:", "alarm_folder": "Alarms", "alarm_prefix": "alarm:"},
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
    assert out.strip() == ("['written_by'] ('contains', 'written_by') Not in the catalog. "
                           "You extract facts from the catalog notes of a library.")
