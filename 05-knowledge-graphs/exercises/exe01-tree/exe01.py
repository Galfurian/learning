"""EXE01 — the data model as a tree. Task: see README.md in this folder."""

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
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_parse(parse_model, __file__)
