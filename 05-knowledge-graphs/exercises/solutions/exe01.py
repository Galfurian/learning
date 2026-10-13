"""EXE01 — the data model as a tree. Reference solution."""

from typing import Any

from kglab.graph import Graph, Node
from kglab.parse import FORMAT, LINE, alarm_id, cell_id
from kglab.runners import run_parse


# TODO: add one device's tree to `graph` and return it. No model: this is a parser.
# data: one YAML file, already loaded: {"device", "name", "kind", "cell", "aliases", "nodes": [...]}.
# file: "models/<name>.yml", for the sources.
#
# Nodes (graph.add_node(Node(id, type, name, aliases, props))):
# - LINE (type FORMAT["root_type"], name FORMAT["root_name"]); the device (type "Device", its name,
#   its aliases, props {"kind": ...}); the cell cell_id(data["cell"]) (type "Cell", name = the key) if any;
# - folders, variables, methods: id "<parent id>/<Name>"; parameters and returns: "<method id>/<name>";
# - a variable directly inside a folder named FORMAT["alarm_folder"] also gets an Alarm node
#   alarm_id(device, name), name = the variable's name, props {"flag": <variable id>}.
# Edges (graph.add_triple(s, relation, o, source)):
# - LINE contains cell, cell contains device (or LINE contains device when there is no cell): source "<file>#";
# - parent contains folder; parent exposes_variable variable; parent exposes_method method;
#   method has_parameter parameter; method returns variable; device has_alarm alarm;
#   source "<file>#<path inside the device>", e.g. "models/rover1.yml#Status/Busy"
#   (parameters and returns share their method's source).
# Variable props: {"type", "initial", "description"}; Method and Folder props: {"description"};
# Parameter props: {"type", "description"}; a `display` key, if present, is the node's only alias.
# Tip: a recursive walk(items, parent_id, path, in_alarms) does the folders.
def parse_model(data: dict[str, Any], file: str, graph: Graph) -> Graph:
    device = data["device"]
    graph.add_node(Node(LINE, FORMAT["root_type"], FORMAT["root_name"]))
    graph.add_node(Node(device, "Device", data.get("name", device), list(data.get("aliases", [])),
                        props={"kind": data.get("kind", "")}))
    if data.get("cell"):
        cell = cell_id(data["cell"])
        graph.add_node(Node(cell, "Cell", data["cell"]))
        graph.add_triple(LINE, "contains", cell, f"{file}#")
        graph.add_triple(cell, "contains", device, f"{file}#")
    else:
        graph.add_triple(LINE, "contains", device, f"{file}#")

    def alias(item: dict[str, Any]) -> list[str]:
        return [item["display"]] if item.get("display") else []

    def walk(items: list[dict[str, Any]], parent: str, path: list[str], in_alarms: bool) -> None:
        for item in items or []:
            name = item.get("folder") or item.get("variable") or item.get("method")
            node, where = f"{parent}/{name}", f"{file}#{'/'.join(path + [name])}"
            if "folder" in item:
                graph.add_node(Node(node, "Folder", name, props={"description": item.get("description", "")}))
                graph.add_triple(parent, "contains", node, where)
                walk(item.get("children", []), node, path + [name], name == FORMAT["alarm_folder"])
            elif "variable" in item:
                graph.add_node(Node(node, "Variable", name, alias(item), props={
                    "type": item.get("type", ""), "initial": item.get("initial"),
                    "description": item.get("description", "")}))
                graph.add_triple(parent, "exposes_variable", node, where)
                if in_alarms:
                    graph.add_node(Node(alarm_id(device, name), "Alarm", name, alias(item), props={"flag": node}))
                    graph.add_triple(device, "has_alarm", alarm_id(device, name), where)
            else:
                graph.add_node(Node(node, "Method", name, alias(item),
                                    props={"description": item.get("description", "")}))
                graph.add_triple(parent, "exposes_method", node, where)
                for p in item.get("parameters", []) or []:
                    graph.add_node(Node(f"{node}/{p['name']}", "Parameter", p["name"], props={
                        "type": p.get("type", ""), "description": p.get("description", "")}))
                    graph.add_triple(node, "has_parameter", f"{node}/{p['name']}", where)
                for r in item.get("returns", []) or []:
                    graph.add_node(Node(f"{node}/{r['name']}", "Variable", r["name"], props={
                        "type": r.get("type", ""), "description": r.get("description", "")}))
                    graph.add_triple(node, "returns", f"{node}/{r['name']}", where)

    walk(data.get("nodes", []), device, [], False)
    return graph


if __name__ == "__main__":
    run_parse(parse_model, __file__)
