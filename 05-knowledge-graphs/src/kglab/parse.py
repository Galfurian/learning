"""The data model as a tree: YAML in, nodes and typed edges out. No model.

A device file holds folders, variables and methods, nested. Every node gets a
path id (`rover1/Status/Busy`) and every edge the place in the file that
states it (`models/rover1.yml#Status/Busy`). The YAML has no edge between
devices: those links are in the prose, and EXE03 extracts them.
"""

from pathlib import Path
from typing import Any

import yaml

from .corpus import MODELS_DIR, Chunk
from .graph import Graph, Node
from .scenario import SCENARIO

# The "opcua-yaml" format, with its names from the scenario.
FORMAT = SCENARIO.data_model
if FORMAT.get("format") != "opcua-yaml":
    raise ValueError(f"parse.py reads the 'opcua-yaml' data model format, not {FORMAT.get('format')!r}")
LINE = FORMAT["root"]
ALARM_FOLDER = FORMAT["alarm_folder"]
T = FORMAT["types"]          # node type of each YAML element: device, cell, folder, variable, ...
R = FORMAT["relations"]      # relation name of each tree edge: contains, exposes_variable, ...


def cell_id(key: str) -> str:
    return f"{FORMAT['cell_prefix']}{key}"


def alarm_id(device: str, name: str) -> str:
    return f"{FORMAT['alarm_prefix']}{device}/{name}"


def display(item: dict[str, Any]) -> list[str]:
    """The display name, as an OPC-UA DisplayName next to the BrowseName: "Low air pressure"."""
    return [item["display"]] if item.get("display") else []


def parse_model(data: dict[str, Any], file: str, graph: Graph | None = None) -> Graph:
    """Add one device's tree to `graph` (a new graph if None)."""
    graph = graph if graph is not None else Graph()
    device = data["device"]
    graph.add_node(Node(LINE, FORMAT["root_type"], FORMAT["root_name"]))
    # Short names come from the asset register (the `aliases` key), not from the OPC-UA tree.
    graph.add_node(Node(device, T["device"], data.get("name", device), list(data.get("aliases", [])),
                        props={"kind": data.get("kind", "")}))
    if data.get("cell"):
        cell = cell_id(data["cell"])
        graph.add_node(Node(cell, T["cell"], data["cell"]))
        graph.add_triple(LINE, R["contains"], cell, f"{file}#")
        graph.add_triple(cell, R["contains"], device, f"{file}#")
    else:
        graph.add_triple(LINE, R["contains"], device, f"{file}#")

    def walk(items: list[dict[str, Any]], parent: str, path: list[str], in_alarms: bool) -> None:
        for item in items or []:
            if "folder" in item:
                name = item["folder"]
                node = f"{parent}/{name}"
                graph.add_node(Node(node, T["folder"], name, props={"description": item.get("description", "")}))
                graph.add_triple(parent, R["contains"], node, f"{file}#{'/'.join(path + [name])}")
                walk(item.get("children", []), node, path + [name], name == ALARM_FOLDER)
            elif "variable" in item:
                name = item["variable"]
                node = f"{parent}/{name}"
                where = f"{file}#{'/'.join(path + [name])}"
                graph.add_node(Node(node, T["variable"], name, display(item), props={
                    "type": item.get("type", ""), "initial": item.get("initial"),
                    "description": item.get("description", "")}))
                graph.add_triple(parent, R["exposes_variable"], node, where)
                if in_alarms:
                    alarm = alarm_id(device, name)
                    graph.add_node(Node(alarm, T["alarm"], name, display(item), props={"flag": node}))
                    graph.add_triple(device, R["has_alarm"], alarm, where)
            elif "method" in item:
                name = item["method"]
                node = f"{parent}/{name}"
                where = f"{file}#{'/'.join(path + [name])}"
                graph.add_node(Node(node, T["method"], name, display(item), props={"description": item.get("description", "")}))
                graph.add_triple(parent, R["exposes_method"], node, where)
                for p in item.get("parameters", []) or []:
                    pid = f"{node}/{p['name']}"
                    graph.add_node(Node(pid, T["parameter"], p["name"], props={
                        "type": p.get("type", ""), "description": p.get("description", "")}))
                    graph.add_triple(node, R["has_parameter"], pid, where)
                for r in item.get("returns", []) or []:
                    rid = f"{node}/{r['name']}"
                    graph.add_node(Node(rid, T["variable"], r["name"], props={
                        "type": r.get("type", ""), "description": r.get("description", "")}))
                    graph.add_triple(node, R["returns"], rid, where)
            else:
                raise ValueError(f"{file}: item under {parent} is not a folder, variable or method: {item!r}")

    walk(data.get("nodes", []), device, [], False)
    return graph


def load_models(directory: Path = MODELS_DIR, graph: Graph | None = None) -> Graph:
    graph = graph if graph is not None else Graph()
    files = sorted(Path(directory).glob("*.yml"))
    if not files:
        raise ValueError(f"no data models in {directory}")
    for path in files:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        parse_model(data, f"models/{path.name}", graph)
    return graph


def model_chunks(directory: Path = MODELS_DIR) -> list[Chunk]:
    """The data models as text chunks, one per top-level folder or method, for chunk RAG (pipeline A).

    Chunk ids are the model paths (`rover1/Status`), so a question's
    `relevant` list can point at them.
    """
    chunks: list[Chunk] = []
    for path in sorted(Path(directory).glob("*.yml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        device, title = data["device"], f"{data.get('name', data['device'])} data model"
        for item in data.get("nodes", []) or []:
            name = item.get("folder") or item.get("method") or item.get("variable")
            cid = f"{device}/{name}"
            text = "\n".join(render(item, 0))
            chunks.append(Chunk(cid, cid, title, name, text))
    return chunks


def render(item: dict[str, Any], depth: int) -> list[str]:
    pad = "  " * depth
    if "folder" in item:
        lines = [f"{pad}folder {item['folder']}: {item.get('description', '')}".rstrip(": ")]
        for child in item.get("children", []) or []:
            lines += render(child, depth + 1)
        return lines
    if "variable" in item:
        initial = f" = {item['initial']}" if item.get("initial") is not None else ""
        return [f"{pad}variable {item['variable']} ({item.get('type', '')}{initial}): {item.get('description', '')}"]
    params = ", ".join(f"{p['name']}: {p.get('type', '')}" for p in item.get("parameters", []) or [])
    returns = ", ".join(f"{r['name']}: {r.get('type', '')}" for r in item.get("returns", []) or [])
    return [f"{pad}method {item['method']}({params}) -> ({returns}): {item.get('description', '')}"]
