import json
import re
from pathlib import Path

import yaml
from kglab.parse import load_models
from kglab.scenario import SCENARIO
from kglab.world import World


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


def sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


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


def test_gold_graph_matches_the_scenario_contract():
    gold = json.loads((DATA / "gold.json").read_text(encoding="utf-8"))
    node_by_id = {node["id"]: node for node in gold["nodes"]}
    allowed_types = set(SCENARIO.node_types)
    assert all(node["type"] in allowed_types for node in gold["nodes"])
    for edge in gold["edges"]:
        assert edge["r"] in SCENARIO.relations
        relation = SCENARIO.relations[edge["r"]]
        assert node_by_id[edge["s"]]["type"] in relation.subject
        assert node_by_id[edge["o"]]["type"] in relation.object

    expected_glossary = {
        node["id"] for node in gold["nodes"] if node["type"] in SCENARIO.glossary_types
    }
    assert {node.id for node in World().glossary} == expected_glossary


def test_prose_uses_human_mentions_not_graph_ids():
    text = "\n".join(sections().values())
    gold = json.loads((DATA / "gold.json").read_text(encoding="utf-8"))
    for node in gold["nodes"]:
        node_id = node["id"]
        if ":" in node_id or "/" in node_id:
            assert node_id not in text


def test_prose_sections_are_distinct_and_have_real_content():
    chunks = sections()
    sentence_sets = {chunk_id: sentences(text) for chunk_id, text in chunks.items()}
    for chunk_id, values in sentence_sets.items():
        assert len(values) == len(set(values)), chunk_id
    ids = sorted(sentence_sets)
    for number, left_id in enumerate(ids):
        for right_id in ids[number + 1:]:
            assert len(set(sentence_sets[left_id]) & set(sentence_sets[right_id])) <= 1, (left_id, right_id)

    gold = json.loads((DATA / "gold.json").read_text(encoding="utf-8"))
    edge_counts = {chunk_id: 0 for chunk_id in chunks}
    for edge in gold["edges"]:
        if edge["source"] in edge_counts:
            edge_counts[edge["source"]] += 1
    empty = [chunk_id for chunk_id, count in edge_counts.items() if count == 0]
    assert len(empty) <= len(chunks) * 0.10, empty
    assert max(edge_counts.values()) <= 6


def test_prose_does_not_leak_schema_vocabulary():
    forbidden = {"serves_bay", "next_step", "observed_by", "fixed_by_method", "incident_on",
                 "next step", "observed by", "the incident was on"}
    for chunk_id, text in sections().items():
        lowered = text.lower()
        assert not any(term in lowered for term in forbidden), chunk_id


def test_glossary_mentions_are_present_in_link_sources():
    glossary_types = {"Bay", "Item", "Pallet", "Mission", "Condition", "Incident"}
    gold = json.loads((DATA / "gold.json").read_text(encoding="utf-8"))
    chunks = sections()
    nodes = {node["id"]: node for node in gold["nodes"]}
    for edge in gold["edges"]:
        if edge["source"] not in chunks:
            continue
        text = chunks[edge["source"]].lower()
        for endpoint in (edge["s"], edge["o"]):
            node = nodes[endpoint]
            if node["type"] not in glossary_types:
                continue
            mentions = [node["name"], *node.get("aliases", [])]
            assert any(mention.lower() in text for mention in mentions), (edge, node)


def test_exercise_mentions_are_present_in_their_chunks():
    mentions = json.loads(SCENARIO.path("mentions").read_text(encoding="utf-8"))
    chunks = sections()
    gold = json.loads((DATA / "gold.json").read_text(encoding="utf-8"))
    node_ids = {node["id"] for node in gold["nodes"]}
    keys = {(item["mention"].casefold(), item["chunk"], item["node"]) for item in mentions}
    assert len(keys) == len(mentions)
    assert mentions
    for item in mentions:
        assert item["chunk"] in chunks
        assert item["mention"].casefold() in chunks[item["chunk"]].casefold(), item
        if item["node"] == "<ambiguous>":
            assert item.get("candidates") == ["rover1", "rover2"]
        else:
            assert item["node"] in node_ids, item


def test_each_prose_edge_endpoint_has_a_surface_mention():
    mentions = json.loads(SCENARIO.path("mentions").read_text(encoding="utf-8"))
    covered = {(item["chunk"], item["node"]) for item in mentions}
    gold = json.loads((DATA / "gold.json").read_text(encoding="utf-8"))
    for edge in gold["edges"]:
        if edge["source"].startswith("models/") or edge["source"] == "line":
            continue
        assert (edge["source"], edge["s"]) in covered
        assert (edge["source"], edge["o"]) in covered


def test_gold_tree_matches_independent_generator_contract():
    gold = json.loads((DATA / "gold.json").read_text(encoding="utf-8"))
    parsed = load_models(DATA / "line" / "models")
    gold_tree = {
        (edge["s"], edge["r"], edge["o"])
        for edge in gold["edges"]
        if edge["source"].startswith("models/")
    }
    assert parsed.triples() == gold_tree

    tree_ids = {node_id for triple in gold_tree for node_id in (triple[0], triple[2])}
    gold_nodes = {node["id"]: node for node in gold["nodes"]}
    for node_id in tree_ids:
        actual = parsed.nodes[node_id]
        expected = gold_nodes[node_id]
        assert actual.type == expected["type"]
        assert actual.name == expected["name"]
        assert actual.props == expected["props"]
        if actual.type in {"Variable", "Method", "Alarm"}:
            assert actual.aliases == expected["aliases"]


def test_every_alarm_flag_has_the_same_display_alias_in_gold():
    gold = json.loads((DATA / "gold.json").read_text(encoding="utf-8"))
    gold_nodes = {node["id"]: node for node in gold["nodes"]}

    def alarm_variables(items):
        for item in items or []:
            if item.get("folder") == "Alarms":
                yield from (child for child in item.get("children", []) if "variable" in child)
            elif item.get("folder"):
                yield from alarm_variables(item.get("children", []))

    flags = 0
    for path in sorted((DATA / "line" / "models").glob("*.yml")):
        model = yaml.safe_load(path.read_text(encoding="utf-8"))
        for item in alarm_variables(model["nodes"]):
            flags += 1
            assert item.get("display"), (path, item)
            alarm = gold_nodes[f"alarm:{model['device']}/{item['variable']}"]
            assert alarm["aliases"] == [item["display"]]
    assert flags >= 30


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
    assert 40 <= manifest["prose_chunks"] <= 60
    assert manifest["words_per_section"]["min"] >= 30
    assert manifest["words_per_section"]["max"] <= 120
    assert 120 <= manifest["link_edges"] <= 200
    assert manifest["estimated_extraction_seconds"] is None
