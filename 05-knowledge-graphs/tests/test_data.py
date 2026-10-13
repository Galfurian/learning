import json
import re
from pathlib import Path

import yaml
from kglab.parse import load_models


ROOT = Path(__file__).parents[1]
DATA = ROOT / "data"


def sections() -> dict[str, str]:
    out: dict[str, str] = {}
    heading = re.compile(r"^## .+ \{#([^}]+)\}")
    for path in sorted((DATA / "line" / "notes").glob("*.md")):
        current: str | None = None
        body: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            match = heading.match(line)
            if match:
                if current is not None:
                    out[current] = "\n".join(body)
                current, body = match.group(1), []
            elif current is not None:
                body.append(line)
        if current is not None:
            out[current] = "\n".join(body)
    return out


def mentions(node: dict, node_id: str) -> set[str]:
    values = {node_id, node.get("name", ""), *node.get("aliases", [])}
    if ":" in node_id:
        values.add(node_id.rsplit(":", 1)[-1])
    if "/" in node_id:
        values.add(node_id.rsplit("/", 1)[-1])
    return {value for value in values if value}


def test_models_are_valid_yaml():
    models = sorted((DATA / "line" / "models").glob("*.yml"))
    assert len(models) == 8
    for path in models:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["device"] == path.stem
        assert data["nodes"]
        assert data["name"]


def test_gold_node_ids_are_unique_and_sources_exist():
    gold = json.loads((DATA / "gold.json").read_text(encoding="utf-8"))
    assert len(gold["nodes"]) == len({node["id"] for node in gold["nodes"]})
    chunks = sections()
    node_by_id = {node["id"]: node for node in gold["nodes"]}
    assert len(chunks) <= 150
    for edge in gold["edges"]:
        assert edge["s"] in node_by_id
        assert edge["o"] in node_by_id
        source = edge["source"]
        if source.startswith("models/") or source == "line":
            continue
        assert source in chunks, source
        text = chunks[source]
        assert any(value in text for value in mentions(node_by_id[edge["s"]], edge["s"])), edge
        assert any(value in text for value in mentions(node_by_id[edge["o"]], edge["o"])), edge


def test_gold_tree_matches_independent_generator_contract():
    gold = json.loads((DATA / "gold.json").read_text(encoding="utf-8"))
    parsed = load_models(DATA / "line" / "models")
    gold_tree = {
        (edge["s"], edge["r"], edge["o"])
        for edge in gold["edges"]
        if edge["source"].startswith("models/")
    }
    assert parsed.triples() == gold_tree


def test_prose_edges_are_distributed_and_schema_is_used():
    gold = json.loads((DATA / "gold.json").read_text(encoding="utf-8"))
    prose_edges = [edge for edge in gold["edges"] if not edge["source"].startswith("models/") and edge["source"] != "line"]
    counts: dict[str, int] = {}
    for edge in prose_edges:
        counts[edge["r"]] = counts.get(edge["r"], 0) + 1
    for relation in {"serves_bay", "moves", "requires", "observed_by", "confirms", "stops", "next_step",
                     "incident_on", "raised", "fixed_by_method"}:
        assert counts.get(relation, 0) >= 2, (relation, counts)


def test_manifest_budget():
    manifest = json.loads((DATA / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["prose_chunks"] <= 150
    assert manifest["estimated_extraction_seconds"] is None
