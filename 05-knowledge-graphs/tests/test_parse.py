from kglab.graph import follow
from kglab.parse import model_chunks, parse_model

MODEL = {
    "device": "rover1",
    "name": "Rover R-1",
    "kind": "mobile robot",
    "cell": None,
    "nodes": [
        {"folder": "Status", "description": "Mission status.", "children": [
            {"variable": "Busy", "type": "bool", "initial": False, "description": "True while a mission runs."},
        ]},
        {"folder": "Alarms", "children": [{"variable": "BumperHit", "type": "bool"}]},
        {"method": "StartMission", "description": "Starts a mission.",
         "parameters": [{"name": "mission", "type": "string"}],
         "returns": [{"name": "submitted", "type": "bool"}]},
    ],
}


def test_tree_edges_and_sources():
    g = parse_model(MODEL, "models/rover1.yml")
    assert follow(g, ["line:main"], ["contains"]) == ["rover1"]
    assert follow(g, ["rover1"], ["contains", "exposes_variable"]) == ["rover1/Alarms/BumperHit", "rover1/Status/Busy"]
    assert follow(g, ["rover1"], ["exposes_method", "has_parameter"]) == ["rover1/StartMission/mission"]
    assert follow(g, ["rover1"], ["exposes_method", "returns"]) == ["rover1/StartMission/submitted"]
    assert follow(g, ["rover1"], ["has_alarm"]) == ["alarm:rover1/BumperHit"]
    busy = g.edges_on("rover1/Status", "exposes_variable")[0]
    assert busy.source == "models/rover1.yml#Status/Busy"


def test_cell_sits_between_line_and_device():
    g = parse_model({**MODEL, "cell": "qc"}, "models/rover1.yml")
    assert follow(g, ["line:main"], ["contains", "contains"]) == ["rover1"]
    assert follow(g, ["line:main"], ["contains"]) == ["cell:qc"]


def test_model_chunks(tmp_path):
    import yaml
    (tmp_path / "rover1.yml").write_text(yaml.safe_dump(MODEL))
    chunks = model_chunks(tmp_path)
    assert [c.id for c in chunks] == ["rover1/Status", "rover1/Alarms", "rover1/StartMission"]
    assert "variable Busy (bool = False)" in chunks[0].text
    assert "method StartMission(mission: string) -> (submitted: bool)" in chunks[2].text


def test_display_name_becomes_alias_and_camel_case_normalizes():
    from kglab.resolve import Resolver
    model = {**MODEL, "nodes": [{"folder": "Alarms", "children": [
        {"variable": "NoAirPressure", "display": "Low air pressure", "type": "bool"}]}]}
    g = parse_model(model, "models/rover1.yml")
    assert g.nodes["alarm:rover1/NoAirPressure"].aliases == ["Low air pressure"]
    r = Resolver(g, types=("Alarm",))
    assert r.resolve("low air pressure").node == "alarm:rover1/NoAirPressure"
    assert r.resolve("no air pressure").node == "alarm:rover1/NoAirPressure"
