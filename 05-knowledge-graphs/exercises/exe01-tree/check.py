from kglab.checks import run_checks
from kglab.graph import Graph, follow

MODEL = {
    "device": "press1", "name": "Press P-1", "kind": "press", "cell": "forming", "aliases": ["P-1"],
    "nodes": [
        {"folder": "Status", "description": "State.", "children": [
            {"variable": "Busy", "type": "bool", "initial": False, "description": "Running."},
            {"folder": "Deep", "children": [{"variable": "Hot", "type": "bool"}]},
        ]},
        {"folder": "Alarms", "children": [{"variable": "NoOil", "type": "bool", "display": "Low oil"}]},
        {"method": "Stamp", "description": "Stamps.", "parameters": [{"name": "force", "type": "number"}],
         "returns": [{"name": "done", "type": "bool"}]},
    ],
}


def checks(exe, check):
    done, g = check.calls(exe.parse_model, MODEL, "models/press1.yml", Graph())
    if not done:
        return
    check.ok(isinstance(g, Graph), "returns the graph", type(g))
    check.ok(follow(g, ["line:main"], ["contains"]) == ["cell:forming"], "the line contains the cell",
             follow(g, ["line:main"], ["contains"]))
    check.ok(follow(g, ["cell:forming"], ["contains"]) == ["press1"], "the cell contains the device")
    check.ok(g.nodes.get("press1") is not None and g.nodes["press1"].aliases == ["P-1"], "the device keeps its aliases",
             g.nodes.get("press1"))
    folders = follow(g, ["press1", "press1/Status"], ["contains"])
    check.ok(folders == ["press1/Alarms", "press1/Status", "press1/Status/Deep"], "folders nest, with path ids", folders)
    check.ok(follow(g, ["press1/Status/Deep"], ["exposes_variable"]) == ["press1/Status/Deep/Hot"],
             "a variable two folders down", follow(g, ["press1/Status/Deep"], ["exposes_variable"]))
    check.ok(follow(g, ["press1"], ["exposes_method", "has_parameter"]) == ["press1/Stamp/force"], "parameters")
    check.ok(follow(g, ["press1"], ["exposes_method", "returns"]) == ["press1/Stamp/done"], "returns")
    check.ok(follow(g, ["press1"], ["has_alarm"]) == ["alarm:press1/NoOil"], "an alarm node for each flag in Alarms",
             follow(g, ["press1"], ["has_alarm"]))
    alarm = g.nodes.get("alarm:press1/NoOil")
    check.ok(alarm is not None and alarm.aliases == ["Low oil"] and alarm.props.get("flag") == "press1/Alarms/NoOil",
             "the alarm keeps its display name and its flag", alarm)
    check.ok(follow(g, ["press1"], ["has_alarm"]) and not follow(g, ["press1/Status/Deep"], ["has_alarm"]),
             "only variables inside Alarms are alarms")
    sources = {(e.s, e.o): e.source for e in g.edges}
    check.ok(sources.get(("press1/Status/Deep", "press1/Status/Deep/Hot")) == "models/press1.yml#Status/Deep/Hot",
             "the source is the file and the path inside the device", sources.get(("press1/Status/Deep", "press1/Status/Deep/Hot")))
    check.ok(sources.get(("press1/Stamp", "press1/Stamp/force")) == "models/press1.yml#Stamp", "parameters share the method's source")
    check.ok(sources.get(("cell:forming", "press1")) == "models/press1.yml#", "line and cell edges: the file only")
    busy = g.nodes.get("press1/Status/Busy")
    check.ok(busy is not None and busy.props.get("initial") is False and busy.type == "Variable", "variable type and props", busy)
    nocell = check.calls(exe.parse_model, {**MODEL, "cell": None}, "models/press1.yml", Graph())[1]
    check.ok(follow(nocell, ["line:main"], ["contains"]) == ["press1"], "no cell: the line contains the device")


run_checks(checks, __file__.replace("check.py", "exe01.py"))
