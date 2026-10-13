"""Build the small, invented production line used by unit 05.

The data model is deliberately YAML-like and deterministic.  It borrows the
shape of an OPC-UA tree, not text or identifiers from any external system.
Run from this directory with ``uv run python data/build.py``.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "line" / "models"
NOTES = ROOT / "line" / "notes"
GOLD = ROOT / "gold.json"
MANIFEST = ROOT / "manifest.json"
SEED = 5


def variable(name: str, kind: str, initial: Any, description: str) -> dict[str, Any]:
    return {"variable": name, "type": kind, "initial": initial, "description": description}


def method(name: str, description: str, parameters: list[dict[str, str]] | None = None,
           returns: list[dict[str, str]] | None = None) -> dict[str, Any]:
    return {"method": name, "description": description,
            "parameters": parameters or [], "returns": returns or []}


def folder(name: str, description: str, children: list[dict[str, Any]]) -> dict[str, Any]:
    return {"folder": name, "description": description, "children": children}


def status() -> dict[str, Any]:
    return folder("Status", "Current device state.", [
        variable("Busy", "bool", False, "True while the current operation runs."),
        variable("CurrentMission", "string", "", "Name of the active mission."),
        variable("LastResult", "string", "idle", "Result of the last operation."),
    ])


def alarm_folder() -> dict[str, Any]:
    return folder("Alarms", "Alarm flags reported by the device.", [
        variable("NoAirPressure", "bool", False, "The air supply is below the safe level."),
        variable("EmergencyStop", "bool", False, "An emergency stop is active."),
        variable("MotorTrip", "bool", False, "The drive motor has tripped."),
        variable("RFIDFault", "bool", False, "A pallet RFID read failed."),
    ])


def reset_method() -> dict[str, Any]:
    return method("ResetAlarms", "Clears alarms after the cause is safe.",
                   [{"name": "mask", "type": "string", "description": "Alarm group to clear."}],
                   [{"name": "done", "type": "bool", "description": "True when the reset is accepted."}])


def models() -> list[dict[str, Any]]:
    return [
        {"device": "conveyor", "name": "Loop Conveyor", "kind": "pallet conveyor", "cell": "cell:conveyor",
         "nodes": [status(), alarm_folder(), reset_method(), method("MovePallet", "Moves one pallet to a bay.",
             [{"name": "pallet", "type": "string", "description": "Pallet identifier."},
              {"name": "bay", "type": "string", "description": "Destination bay."}],
             [{"name": "accepted", "type": "bool", "description": "True when the move is queued."}])]},
        {"device": "warehouse", "name": "Vertical Warehouse", "kind": "vertical warehouse", "cell": "cell:warehouse",
         "nodes": [status(), folder("Inventory", "Trays and stock state.", [
             variable("TrayInBay", "string", "", "Tray currently at the operator bay."),
             variable("StockReady", "bool", True, "True when the requested tray can be handled."),
         ]), alarm_folder(), reset_method(), method("ExtractTray", "Brings a tray to the operator bay.",
             [{"name": "tray", "type": "string", "description": "Tray identifier."}],
             [{"name": "accepted", "type": "bool", "description": "True when extraction is queued."}]),
         method("SendBack", "Returns the tray from the operator bay.", returns=[
             {"name": "done", "type": "bool", "description": "True when return is accepted."}])]},
        {"device": "rover1", "name": "Rover R-1", "kind": "mobile robot", "cell": "cell:transport",
         "nodes": [status(), folder("Motion", "Motion commands.", [
             method("StartMission", "Starts a named delivery mission.",
                    [{"name": "mission", "type": "string", "description": "Mission identifier."}],
                    [{"name": "submitted", "type": "bool", "description": "True when accepted."}]),
             method("StopMission", "Stops the active delivery mission.", returns=[
                 {"name": "stopped", "type": "bool", "description": "True when stopped."}]),
         ])]},
        {"device": "rover2", "name": "Rover R-2", "kind": "mobile robot", "cell": "cell:transport",
         "nodes": [status(), folder("Motion", "Motion commands.", [
             method("StartMission", "Starts a named delivery mission.",
                    [{"name": "mission", "type": "string", "description": "Mission identifier."}],
                    [{"name": "submitted", "type": "bool", "description": "True when accepted."}]),
             method("StopMission", "Stops the active delivery mission.", returns=[
                 {"name": "stopped", "type": "bool", "description": "True when stopped."}]),
         ])]},
        {"device": "tester", "name": "Board Tester", "kind": "test cell", "cell": "cell:test",
         "nodes": [status(), folder("Boards", "Board transfer and test operations.", [
             method("BoardIn", "Accepts a board at the input bay.", returns=[
                 {"name": "accepted", "type": "bool", "description": "True when accepted."}]),
             method("RunTest", "Runs the board test.",
                    [{"name": "serial", "type": "string", "description": "Board serial number."}],
                    [{"name": "started", "type": "bool", "description": "True when the test starts."}]),
             method("BoardOut", "Releases a tested board.", returns=[
                 {"name": "done", "type": "bool", "description": "True when released."}]),
             variable("TestPassed", "bool", False, "Result of the last board test."),
         ])]},
        {"device": "cnc", "name": "Engraving Cell", "kind": "CNC and arm", "cell": "cell:cnc",
         "nodes": [status(), folder("Arm", "Arm and spindle operations.", [
             variable("AtPallet", "bool", False, "True when the arm is at the pallet."),
             method("PickBoard", "Picks a board from the pallet.", returns=[
                 {"name": "done", "type": "bool", "description": "True when picked."}]),
             method("Engrave", "Engraves the board identifier.",
                    [{"name": "serial", "type": "string", "description": "Board serial number."}],
                    [{"name": "done", "type": "bool", "description": "True when engraving is complete."}]),
             method("PlaceBoard", "Places the board on the pallet.", returns=[
                 {"name": "done", "type": "bool", "description": "True when placed."}]),
         ])]},
        {"device": "assembly", "name": "Assembly Cell", "kind": "assembly PLC and arms", "cell": "cell:assembly",
         "nodes": [status(), folder("Alarms", "Assembly alarm flags.", [
             variable("EmergencyStop", "bool", False, "An emergency stop is active."),
             variable("ScrewdriverFault", "bool", False, "The screwdriver reports a fault."),
         ]), reset_method(), folder("Assembly", "Assembly operations.", [
             method("Assemble", "Fits the covers to the board.",
                    [{"name": "board", "type": "string", "description": "Board identifier."}],
                    [{"name": "done", "type": "bool", "description": "True when assembled."}]),
             method("Screw", "Runs the screwdriver program.",
                    [{"name": "program", "type": "string", "description": "Screwdriver program."}],
                    [{"name": "done", "type": "bool", "description": "True when complete."}]),
         ])]},
        {"device": "qc", "name": "Camera Quality Cell", "kind": "camera quality control", "cell": "cell:qc",
         "nodes": [status(), folder("Inspection", "Pallet inspection operations.", [
             method("CheckPallet", "Checks the assembled pallet.",
                    [{"name": "pallet", "type": "string", "description": "Pallet identifier."}],
                    [{"name": "passed", "type": "bool", "description": "True when all checks pass."}]),
             variable("Passed", "bool", False, "Result of the last pallet inspection."),
             variable("ChecksTotal", "number", 0, "Number of completed inspections."),
         ])]},
    ]


def iter_children(nodes: list[dict[str, Any]], prefix: str) -> list[tuple[str, str, str | None, dict[str, Any]]]:
    """Return (id, type, parent, node) for folders, variables and methods."""
    result: list[tuple[str, str, str | None, dict[str, Any]]] = []
    for node in nodes:
        key = next(k for k in ("folder", "variable", "method") if k in node)
        name = str(node[key])
        node_id = f"{prefix}/{name}"
        kind = {"folder": "Folder", "variable": "Variable", "method": "Method"}[key]
        result.append((node_id, kind, prefix, node))
        if key == "folder":
            result.extend(iter_children(node.get("children", []), node_id))
    return result


def display(node: dict[str, Any]) -> str:
    return str(node.get("folder", node.get("variable", node.get("method", ""))))


def model_graph(model: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    device = model["device"]
    nodes = [{"id": device, "type": "Device", "name": model["name"],
              "aliases": (["the first rover", "R-1"] if device == "rover1" else
                          ["the second rover", "R-2"] if device == "rover2" else []), "props": {"kind": model["kind"], "cell": model["cell"]}}]
    edges: list[dict[str, str]] = []
    for node_id, kind, parent, node in iter_children(model["nodes"], device):
        nodes.append({"id": node_id, "type": kind, "name": display(node), "aliases": [], "props": {"type": node.get("type")} })
        source = f"models/{device}.yml#{node_id[len(device) + 1:]}"
        if kind == "Folder":
            edges.append({"s": parent, "r": "contains", "o": node_id, "source": source})
        elif kind == "Variable":
            edges.append({"s": parent, "r": "exposes_variable", "o": node_id, "source": source})
            if parent.endswith("/Alarms"):
                alarm_id = f"alarm:{device}/{node['variable']}"
                nodes.append({"id": alarm_id, "type": "Alarm", "name": str(node["variable"]), "aliases": [], "props": {}})
                edges.append({"s": device, "r": "has_alarm", "o": alarm_id, "source": source})
        else:
            edges.append({"s": parent, "r": "exposes_method", "o": node_id, "source": source})
            for item in node.get("parameters", []):
                parameter_id = f"{node_id}/{item['name']}"
                nodes.append({"id": parameter_id, "type": "Parameter", "name": item["name"], "aliases": [], "props": {"type": item["type"]}})
                edges.append({"s": node_id, "r": "has_parameter", "o": parameter_id, "source": source})
            for item in node.get("returns", []):
                return_id = f"{node_id}/{item['name']}"
                nodes.append({"id": return_id, "type": "Variable", "name": item["name"], "aliases": [], "props": {"type": item["type"], "return": True}})
                edges.append({"s": node_id, "r": "returns", "o": return_id, "source": source})
    return nodes, edges


def prose() -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, str]]]:
    notes: dict[str, list[dict[str, Any]]] = {}
    links: list[dict[str, str]] = []

    def add(file: str, chunk: str, text: str, edges: list[tuple[str, str, str]]) -> None:
        notes.setdefault(file, []).append({"id": chunk, "title": chunk.replace("-", " ").title(), "text": text})
        for s, r, o in edges:
            links.append({"s": s, "r": r, "o": o, "source": chunk})

    add("conveyor.md", "conveyor-route", "The Loop Conveyor serves bay 1 and bay 2. MovePallet moves pallet:7 to bay:1, then to bay:2. The conveyor requires cond:conveyor/ready, observed by conveyor/Status/Busy.", [
        ("conveyor", "serves_bay", "bay:1"), ("conveyor", "serves_bay", "bay:2"), ("conveyor", "moves", "pallet:7"), ("conveyor/MovePallet", "requires", "cond:conveyor/ready"), ("cond:conveyor/ready", "observed_by", "conveyor/Status/Busy")])
    add("conveyor.md", "conveyor-alarms", "The conveyor alarm:conveyor/NoAirPressure stops assembly and alarm:conveyor/MotorTrip stops qc. ResetAlarms fixes both alarms after the line is safe.", [
        ("alarm:conveyor/NoAirPressure", "stops", "assembly"), ("alarm:conveyor/MotorTrip", "stops", "qc")])
    add("warehouse.md", "warehouse-operations", "The Vertical Warehouse serves bay 5. ExtractTray requires cond:warehouse/idle, observed by warehouse/Status/Busy, and moves item:tray. SendBack also moves item:tray.", [
        ("warehouse", "serves_bay", "bay:5"), ("warehouse/ExtractTray", "requires", "cond:warehouse/idle"), ("cond:warehouse/idle", "observed_by", "warehouse/Status/Busy"), ("warehouse", "moves", "item:tray")])
    add("warehouse.md", "warehouse-reset", "The warehouse alarm reset uses warehouse/ResetAlarms. Its operation needs cond:warehouse/stock-ready, observed by warehouse/Inventory/StockReady, and the result is warehouse/ResetAlarms/done.", [
        ("warehouse/ResetAlarms", "requires", "cond:warehouse/stock-ready"), ("cond:warehouse/stock-ready", "observed_by", "warehouse/Inventory/StockReady")])
    add("rovers.md", "rovers-missions", "Rover R-1, also called the first rover, serves bay 5 and moves item:board from the warehouse to pallet:7. StartMission requires cond:rover/idle, observed by rover1/Status/Busy. Rover R-2 serves bay 5 too.", [
        ("rover1", "serves_bay", "bay:5"), ("rover1", "moves", "item:board"), ("rover1/Motion/StartMission", "requires", "cond:rover/idle"), ("cond:rover/idle", "observed_by", "rover1/Status/Busy"), ("rover2", "serves_bay", "bay:5")])
    add("rovers.md", "rovers-confirm", "The rover mission:rover/deliver-board is confirmed by rover1/Status/LastResult. The second rover, or R-2, can also move item:cover to pallet:7.", [
        ("rover1/Status/LastResult", "confirms", "mission:rover/deliver-board"), ("rover2", "moves", "item:cover")])
    add("tester.md", "tester-route", "The Board Tester serves bay 2 and moves item:board to cell:cnc. BoardIn requires cond:tester/ready, observed by tester/Status/Busy.", [
        ("tester", "serves_bay", "bay:2"), ("tester", "moves", "item:board"), ("tester/Boards/BoardIn", "requires", "cond:tester/ready"), ("cond:tester/ready", "observed_by", "tester/Status/Busy")])
    add("tester.md", "tester-result", "The test mission:tester/board-test is confirmed by tester/Boards/TestPassed. RunTest returns tester/Boards/RunTest/started.", [
        ("tester/Boards/TestPassed", "confirms", "mission:tester/board-test")])
    add("cnc.md", "cnc-route", "The Engraving Cell serves bay 3 and moves item:board. PickBoard requires cond:cnc/idle, observed by cnc/Status/Busy.", [
        ("cnc", "serves_bay", "bay:3"), ("cnc", "moves", "item:board"), ("cnc/Arm/PickBoard", "requires", "cond:cnc/idle"), ("cond:cnc/idle", "observed_by", "cnc/Status/Busy")])
    add("cnc.md", "cnc-confirm", "The engraving mission:cnc/engrave-board is confirmed by cnc/Status/LastResult. PlaceBoard moves item:board to pallet:7.", [
        ("cnc/Status/LastResult", "confirms", "mission:cnc/engrave-board"), ("cnc", "moves", "item:board")])
    add("assembly.md", "assembly-route", "The Assembly Cell serves bay 4 and moves item:cover-top and item:cover-bottom onto pallet:7. Assemble requires cond:assembly/idle, observed by assembly/Status/Busy.", [
        ("assembly", "serves_bay", "bay:4"), ("assembly", "moves", "item:cover-top"), ("assembly", "moves", "item:cover-bottom"), ("assembly/Assembly/Assemble", "requires", "cond:assembly/idle"), ("cond:assembly/idle", "observed_by", "assembly/Status/Busy")])
    add("assembly.md", "assembly-confirm", "The assembly mission:assembly/fit-covers is confirmed by assembly/Status/LastResult. Screw requires cond:assembly/screwdriver-ready, observed by assembly/Status/Busy.", [
        ("assembly/Status/LastResult", "confirms", "mission:assembly/fit-covers"), ("assembly/Assembly/Screw", "requires", "cond:assembly/screwdriver-ready"), ("cond:assembly/screwdriver-ready", "observed_by", "assembly/Status/Busy")])
    add("qc.md", "qc-route", "The Camera Quality Cell serves bay 5. CheckPallet requires cond:qc/idle, observed by qc/Status/Busy, and confirms mission:qc/inspect-pallet through qc/Inspection/Passed.", [
        ("qc", "serves_bay", "bay:5"), ("qc/Inspection/CheckPallet", "requires", "cond:qc/idle"), ("cond:qc/idle", "observed_by", "qc/Status/Busy"), ("qc/Inspection/Passed", "confirms", "mission:qc/inspect-pallet")])
    add("qc.md", "qc-result", "The QC mission:qc/inspect-pallet is confirmed by qc/Inspection/Passed. The camera cell moves item:board to the finished pallet record.", [
        ("qc/Inspection/Passed", "confirms", "mission:qc/inspect-pallet"), ("qc", "moves", "item:board")])
    add("line.md", "line-route", "The route is bay:1, then bay:2, bay:3, bay:4, and bay:5. The conveyor next step is bay:2; bay:2 next step is bay:3; bay:3 next step is bay:4; bay:4 next step is bay:5.", [
        ("bay:1", "next_step", "bay:2"), ("bay:2", "next_step", "bay:3"), ("bay:3", "next_step", "bay:4"), ("bay:4", "next_step", "bay:5")])
    add("line.md", "line-stops", "alarm:assembly/EmergencyStop stops conveyor. alarm:conveyor/EmergencyStop stops warehouse. alarm:conveyor/NoAirPressure stops assembly.", [
        ("alarm:assembly/EmergencyStop", "stops", "conveyor"), ("alarm:conveyor/EmergencyStop", "stops", "warehouse"), ("alarm:conveyor/NoAirPressure", "stops", "assembly")])
    add("incidents.md", "incident-rover-alias", "Incident incident:2026-03-04-1: on 2026-03-04, the first rover raised alarm:conveyor/RFIDFault while moving item:board. The incident was on rover1 and rover1/Motion/StopMission fixed it.", [
        ("incident:2026-03-04-1", "incident_on", "rover1"), ("incident:2026-03-04-1", "raised", "alarm:conveyor/RFIDFault"), ("incident:2026-03-04-1", "fixed_by_method", "rover1/Motion/StopMission")])
    add("incidents.md", "incident-rover-second", "Incident incident:2026-03-05-1: on 2026-03-05, R-2 had alarm:assembly/ScrewdriverFault. The incident was on rover2 and rover2/Motion/StopMission fixed it.", [
        ("incident:2026-03-05-1", "incident_on", "rover2"), ("incident:2026-03-05-1", "raised", "alarm:assembly/ScrewdriverFault"), ("incident:2026-03-05-1", "fixed_by_method", "rover2/Motion/StopMission")])
    add("incidents.md", "incident-ambiguous", "Incident incident:2026-03-06-1: on 2026-03-06, the rover raised alarm:conveyor/MotorTrip. The phrase the rover is ambiguous: it can mean rover1 or rover2, so the incident is not linked to one device.", [
        ("incident:2026-03-06-1", "raised", "alarm:conveyor/MotorTrip")])
    return notes, links


def write_model(model: dict[str, Any]) -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    path = MODELS / f"{model['device']}.yml"
    path.write_text(yaml.safe_dump(model, sort_keys=False, allow_unicode=False), encoding="utf-8")


def main() -> None:
    MODELS.mkdir(parents=True, exist_ok=True)
    NOTES.mkdir(parents=True, exist_ok=True)
    for path in MODELS.glob("*.yml"):
        path.unlink()
    for path in NOTES.glob("*.md"):
        path.unlink()

    all_nodes: list[dict[str, Any]] = [
        {"id": "line:main", "type": "Line", "name": "Main Line", "aliases": [], "props": {}},
    ]
    all_edges: list[dict[str, str]] = []
    cells = {
        "cell:conveyor": "Conveyor Cell", "cell:warehouse": "Warehouse Cell", "cell:transport": "Transport Cell",
        "cell:test": "Test Cell", "cell:cnc": "CNC Cell", "cell:assembly": "Assembly Cell", "cell:qc": "QC Cell",
    }
    for cell_id, name in cells.items():
        all_nodes.append({"id": cell_id, "type": "Cell", "name": name, "aliases": [], "props": {}})
        all_edges.append({"s": "line:main", "r": "contains", "o": cell_id, "source": "line"})

    for model in models():
        write_model(model)
        nodes, edges = model_graph(model)
        all_nodes.extend(nodes)
        all_edges.extend(edges)
        all_edges.append({"s": model["cell"], "r": "contains", "o": model["device"], "source": "line"})

    extra_nodes = [
        ("bay:1", "Bay", "Bay 1"), ("bay:2", "Bay", "Bay 2"), ("bay:3", "Bay", "Bay 3"),
        ("bay:4", "Bay", "Bay 4"), ("bay:5", "Bay", "Bay 5"), ("pallet:7", "Pallet", "Pallet 7"),
        ("item:board", "Item", "Board"), ("item:cover", "Item", "Cover"),
        ("item:cover-top", "Item", "Top cover"),
        ("item:cover-bottom", "Item", "Bottom cover"), ("item:tray", "Item", "Tray"),
    ]
    for node_id, kind, name in extra_nodes:
        all_nodes.append({"id": node_id, "type": kind, "name": name, "aliases": [], "props": {}})
    for node_id, kind, name in [
        ("mission:rover/deliver-board", "Mission", "Deliver board"), ("mission:tester/board-test", "Mission", "Test board"),
        ("mission:cnc/engrave-board", "Mission", "Engrave board"), ("mission:assembly/fit-covers", "Mission", "Fit covers"),
        ("mission:qc/inspect-pallet", "Mission", "Inspect pallet"),
    ]:
        all_nodes.append({"id": node_id, "type": kind, "name": name, "aliases": [], "props": {}})
    for node_id, name in [("cond:conveyor/ready", "Conveyor ready"), ("cond:warehouse/idle", "Warehouse idle"),
                          ("cond:warehouse/stock-ready", "Stock ready"), ("cond:rover/idle", "Rover idle"),
                          ("cond:tester/ready", "Tester ready"), ("cond:cnc/idle", "CNC idle"),
                          ("cond:assembly/idle", "Assembly idle"), ("cond:assembly/screwdriver-ready", "Screwdriver ready"),
                          ("cond:qc/idle", "QC idle")]:
        all_nodes.append({"id": node_id, "type": "Condition", "name": name, "aliases": [], "props": {}})
    for incident_id, date in [("incident:2026-03-04-1", "2026-03-04"), ("incident:2026-03-05-1", "2026-03-05"), ("incident:2026-03-06-1", "2026-03-06")]:
        all_nodes.append({"id": incident_id, "type": "Incident", "name": incident_id, "aliases": [], "props": {"date": date}})

    notes, links = prose()
    for file, sections in notes.items():
        path = NOTES / file
        lines = [f"# {file.removesuffix('.md').replace('-', ' ').title()}", ""]
        for section in sections:
            lines += [f"## {section['title']} {{#{section['id']}}}", "", section["text"], ""]
        path.write_text("\n".join(lines), encoding="utf-8")
    all_edges.extend(links)

    # Alias metadata is part of the node, while the deliberately ambiguous alias is separate.
    ambiguous = {"the rover": ["rover1", "rover2"]}
    gold = {"nodes": all_nodes, "edges": all_edges, "ambiguous": ambiguous}
    GOLD.write_text(json.dumps(gold, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    prose_sections = [s for sections in notes.values() for s in sections]
    words = [len(re.findall(r"\S+", s["text"])) for s in prose_sections]
    manifest = {"seed": SEED, "documents": [{"path": f"line/models/{m['device']}.yml", "sections": 0, "mode": "parse"} for m in models()] +
                [{"path": f"line/notes/{name}", "sections": len(sections), "mode": "extract"} for name, sections in notes.items()],
                "prose_chunks": len(prose_sections), "chunk_size": 120, "overlap": 0,
                "words_per_section": {"min": min(words), "mean": round(sum(words) / len(words), 1), "max": max(words)},
                "link_edges": len(links), "estimated_extraction_seconds": None}
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(models())} models, {len(prose_sections)} prose chunks, {len(links)} link edges")


if __name__ == "__main__":
    main()
