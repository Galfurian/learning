"""Build the small, invented production line used by unit 05.

The data model is deliberately YAML-like and deterministic.  It borrows the
shape of an OPC-UA tree, not text or identifiers from any external system.
Run from this directory with ``uv run python data/build.py``.
"""

from __future__ import annotations

import json
import re
from datetime import date as calendar_date
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent
MODELS = ROOT / "line" / "models"
NOTES = ROOT / "line" / "notes"
GOLD = ROOT / "gold.json"
MANIFEST = ROOT / "manifest.json"
SEED = 5


def variable(name: str, kind: str, initial: Any, description: str, *,
             display_name: str | None = None) -> dict[str, Any]:
    node = {"variable": name, "type": kind, "initial": initial, "description": description}
    if display_name:
        node["display"] = display_name
    return node


def method(name: str, description: str, parameters: list[dict[str, str]] | None = None,
           returns: list[dict[str, str]] | None = None, *,
           display_name: str | None = None) -> dict[str, Any]:
    node = {"method": name, "description": description,
            "parameters": parameters or [], "returns": returns or []}
    if display_name:
        node["display"] = display_name
    return node


def folder(name: str, description: str, children: list[dict[str, Any]]) -> dict[str, Any]:
    return {"folder": name, "description": description, "children": children}


def status() -> dict[str, Any]:
    return folder("Status", "Current device state.", [
        variable("Busy", "bool", False, "True while the current operation runs.", display_name="Busy flag"),
        variable("CurrentMission", "string", "", "Name of the active mission.", display_name="Current mission"),
        variable("LastResult", "string", "idle", "Result of the last operation.", display_name="Last result"),
    ])


def alarm_folder() -> dict[str, Any]:
    return folder("Alarms", "Alarm flags reported by the device.", [
        variable("NoAirPressure", "bool", False, "The air supply is below the safe level.", display_name="Low air pressure"),
        variable("EmergencyStop", "bool", False, "An emergency stop is active.", display_name="Emergency stop"),
        variable("MotorTrip", "bool", False, "The drive motor has tripped.", display_name="Motor trip"),
        variable("RFIDFault", "bool", False, "A pallet RFID read failed.", display_name="RFID reader fault"),
    ])


def reset_method() -> dict[str, Any]:
    return method("ResetAlarms", "Clears alarms after the cause is safe.",
                   [{"name": "mask", "type": "string", "description": "Alarm group to clear."}],
                   [{"name": "done", "type": "bool", "description": "True when the reset is accepted."}],
                   display_name="Reset alarms")


def common_diagnostics() -> list[dict[str, Any]]:
    return [
        folder("Statistics", "Counters for the current shift.", [
            variable("CyclesToday", "number", 0, "Completed cycles since the shift started."),
            variable("FaultsToday", "number", 0, "Faults recorded since the shift started."),
            variable("MinutesRunning", "number", 0, "Running minutes since the last reset."),
            variable("LastCycleSeconds", "number", 0, "Duration of the last completed cycle.", display_name="Last cycle time"),
        ]),
        folder("Diagnostics", "Checks used by maintenance staff.", [
            variable("CommunicationOk", "bool", True, "True when the controller answers.", display_name="Communication healthy"),
            variable("SafetyOk", "bool", True, "True when safety inputs are healthy."),
            variable("Firmware", "string", "line-1.0", "Invented controller firmware label."),
            method("ReadDiagnostics", "Reads the maintenance diagnostics.", returns=[
                {"name": "report", "type": "string", "description": "Short diagnostic report."}],
                   display_name="Read diagnostics"),
        ]),
        folder("Maintenance", "Routine service operations.", [
            method("AcknowledgeService", "Records a completed service visit.",
                   [{"name": "note", "type": "string", "description": "Service note."}],
                   [{"name": "accepted", "type": "bool", "description": "True when the note is saved."}],
                   display_name="Acknowledge service"),
            method("ResetCounters", "Resets shift counters after approval.", returns=[
                {"name": "done", "type": "bool", "description": "True when counters are reset."}],
                   display_name="Reset counters"),
        ]),
    ]


def models() -> list[dict[str, Any]]:
    result = [
        {"device": "conveyor", "name": "Loop Conveyor", "kind": "pallet conveyor", "cell": "conveyor",
         "nodes": [status(), alarm_folder(), reset_method(), method("MovePallet", "Moves one pallet to a bay.",
             [{"name": "pallet", "type": "string", "description": "Pallet identifier."},
              {"name": "bay", "type": "string", "description": "Destination bay."}],
             [{"name": "accepted", "type": "bool", "description": "True when the move is queued."}],
             display_name="Move pallet")]},
        {"device": "warehouse", "name": "Vertical Warehouse", "kind": "vertical warehouse", "cell": "warehouse",
         "nodes": [status(), folder("Inventory", "Trays and stock state.", [
             variable("TrayInBay", "string", "", "Tray currently at the operator bay.", display_name="Tray in bay"),
             variable("StockReady", "bool", True, "True when the requested tray can be handled.", display_name="Stock ready"),
         ]), alarm_folder(), reset_method(), method("ExtractTray", "Brings a tray to the operator bay.",
             [{"name": "tray", "type": "string", "description": "Tray identifier."}],
             [{"name": "accepted", "type": "bool", "description": "True when extraction is queued."}],
             display_name="Extract tray"),
         method("SendBack", "Returns the tray from the operator bay.", returns=[
             {"name": "done", "type": "bool", "description": "True when return is accepted."}],
             display_name="Send back")]},
        {"device": "rover1", "name": "Rover R-1", "kind": "mobile robot", "cell": "transport",
         "nodes": [status(), folder("Motion", "Motion commands.", [
             method("StartMission", "Starts a named delivery mission.",
                    [{"name": "mission", "type": "string", "description": "Mission identifier."}],
                    [{"name": "submitted", "type": "bool", "description": "True when accepted."}],
                    display_name="Start mission"),
             method("StopMission", "Stops the active delivery mission.", returns=[
                 {"name": "stopped", "type": "bool", "description": "True when stopped."}],
                 display_name="Stop mission"),
         ])]},
        {"device": "rover2", "name": "Rover R-2", "kind": "mobile robot", "cell": "transport",
         "nodes": [status(), folder("Motion", "Motion commands.", [
             method("StartMission", "Starts a named delivery mission.",
                    [{"name": "mission", "type": "string", "description": "Mission identifier."}],
                    [{"name": "submitted", "type": "bool", "description": "True when accepted."}],
                    display_name="Start mission"),
             method("StopMission", "Stops the active delivery mission.", returns=[
                 {"name": "stopped", "type": "bool", "description": "True when stopped."}],
                 display_name="Stop mission"),
         ])]},
        {"device": "tester", "name": "Board Tester", "kind": "test cell", "cell": "test",
         "nodes": [status(), folder("Boards", "Board transfer and test operations.", [
             method("BoardIn", "Accepts a board at the input bay.", returns=[
                 {"name": "accepted", "type": "bool", "description": "True when accepted."}],
                 display_name="Board in"),
             method("RunTest", "Runs the board test.",
                    [{"name": "serial", "type": "string", "description": "Board serial number."}],
                    [{"name": "started", "type": "bool", "description": "True when the test starts."}],
                    display_name="Run test"),
             method("BoardOut", "Releases a tested board.", returns=[
                 {"name": "done", "type": "bool", "description": "True when released."}],
                 display_name="Board out"),
             variable("TestPassed", "bool", False, "Result of the last board test.", display_name="Test passed"),
         ])]},
        {"device": "cnc", "name": "Engraving Cell", "kind": "CNC and arm", "cell": "cnc",
         "nodes": [status(), folder("Arm", "Arm and spindle operations.", [
             variable("AtPallet", "bool", False, "True when the arm is at the pallet.", display_name="At pallet"),
             method("PickBoard", "Picks a board from the pallet.", returns=[
                 {"name": "done", "type": "bool", "description": "True when picked."}],
                 display_name="Pick board"),
             method("Engrave", "Engraves the board identifier.",
                    [{"name": "serial", "type": "string", "description": "Board serial number."}],
                    [{"name": "done", "type": "bool", "description": "True when engraving is complete."}],
                    display_name="Engrave board"),
             method("PlaceBoard", "Places the board on the pallet.", returns=[
                 {"name": "done", "type": "bool", "description": "True when placed."}],
                 display_name="Place board"),
         ])]},
        {"device": "assembly", "name": "Assembly Cell", "kind": "assembly PLC and arms", "cell": "assembly",
         "nodes": [status(), folder("Alarms", "Assembly alarm flags.", [
             variable("EmergencyStop", "bool", False, "An emergency stop is active.", display_name="Emergency stop"),
             variable("ScrewdriverFault", "bool", False, "The screwdriver reports a fault.", display_name="Screwdriver fault"),
             variable("NoAirPressure", "bool", False, "The air supply is below the safe level.", display_name="Low air pressure"),
             variable("MotorTrip", "bool", False, "The assembly drive has tripped.", display_name="Motor trip"),
         ]), reset_method(), folder("Assembly", "Assembly operations.", [
             method("Assemble", "Fits the covers to the board.",
                    [{"name": "board", "type": "string", "description": "Board identifier."}],
                    [{"name": "done", "type": "bool", "description": "True when assembled."}],
                    display_name="Assemble board"),
             method("Screw", "Runs the screwdriver program.",
                    [{"name": "program", "type": "string", "description": "Screwdriver program."}],
                    [{"name": "done", "type": "bool", "description": "True when complete."}],
                    display_name="Run screwdriver"),
         ])]},
        {"device": "qc", "name": "Camera Quality Cell", "kind": "camera quality control", "cell": "qc",
         "nodes": [status(), folder("Inspection", "Pallet inspection operations.", [
             method("CheckPallet", "Checks the assembled pallet.",
                    [{"name": "pallet", "type": "string", "description": "Pallet identifier."}],
                    [{"name": "passed", "type": "bool", "description": "True when all checks pass."}],
                    display_name="Check pallet"),
             variable("Passed", "bool", False, "Result of the last pallet inspection.", display_name="Inspection passed"),
             variable("ChecksTotal", "number", 0, "Number of completed inspections.", display_name="Checks total"),
             ])]},
    ]
    for model in result:
        if not any(node.get("folder") == "Alarms" for node in model["nodes"]):
            model["nodes"].insert(1, alarm_folder())
        model["nodes"].extend(common_diagnostics())
    return result


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
                          ["the second rover", "R-2"] if device == "rover2" else []), "props": {"kind": model["kind"]}}]
    edges: list[dict[str, str]] = []
    model_file = f"models/{device}.yml"
    if model.get("cell"):
        cell = f"cell:{model['cell']}"
        edges.append({"s": "line:main", "r": "contains", "o": cell, "source": f"{model_file}#"})
        edges.append({"s": cell, "r": "contains", "o": device, "source": f"{model_file}#"})
    else:
        edges.append({"s": "line:main", "r": "contains", "o": device, "source": f"{model_file}#"})
    for node_id, kind, parent, node in iter_children(model["nodes"], device):
        if kind == "Folder":
            props = {"description": node.get("description", "")}
        elif kind == "Variable":
            props = {"type": node.get("type", ""), "initial": node.get("initial"),
                     "description": node.get("description", "")}
        else:
            props = {"description": node.get("description", "")}
        aliases = [node["display"]] if node.get("display") else []
        nodes.append({"id": node_id, "type": kind, "name": display(node), "aliases": aliases, "props": props})
        source = f"{model_file}#{node_id[len(device) + 1:]}"
        if kind == "Folder":
            edges.append({"s": parent, "r": "contains", "o": node_id, "source": source})
        elif kind == "Variable":
            edges.append({"s": parent, "r": "exposes_variable", "o": node_id, "source": source})
            if parent.endswith("/Alarms"):
                alarm_id = f"alarm:{device}/{node['variable']}"
                nodes.append({"id": alarm_id, "type": "Alarm", "name": str(node["variable"]), "aliases": aliases, "props": {"flag": node_id}})
                edges.append({"s": device, "r": "has_alarm", "o": alarm_id, "source": source})
        else:
            edges.append({"s": parent, "r": "exposes_method", "o": node_id, "source": source})
            for item in node.get("parameters", []):
                parameter_id = f"{node_id}/{item['name']}"
                nodes.append({"id": parameter_id, "type": "Parameter", "name": item["name"], "aliases": [],
                              "props": {"type": item["type"], "description": item.get("description", "")}})
                edges.append({"s": node_id, "r": "has_parameter", "o": parameter_id, "source": source})
            for item in node.get("returns", []):
                return_id = f"{node_id}/{item['name']}"
                nodes.append({"id": return_id, "type": "Variable", "name": item["name"], "aliases": [],
                              "props": {"type": item["type"], "description": item.get("description", "")}})
                edges.append({"s": node_id, "r": "returns", "o": return_id, "source": source})
    return nodes, edges


def prose() -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, str]]]:
    notes: dict[str, list[dict[str, Any]]] = {}
    links: list[dict[str, str]] = []

    def add(file: str, chunk: str, text: str, edges: list[tuple[str, str, str]]) -> None:
        notes.setdefault(file, []).append({"id": chunk, "title": chunk.replace("-", " ").title(), "text": text})
        for s, r, o in edges:
            links.append({"s": s, "r": r, "o": o, "source": chunk})

    add("conveyor.md", "conveyor-route", "The Loop Conveyor serves bay 1 and bay 2. MovePallet moves pallet 7 to bay 1, then to bay 2. The line-ready condition is checked from the Busy flag in the Status folder before motion starts. A full loop takes about four minutes at the standard speed.", [
        ("conveyor", "serves_bay", "bay:1"), ("conveyor", "serves_bay", "bay:2"), ("conveyor", "moves", "pallet:7"), ("conveyor/MovePallet", "requires", "cond:conveyor/ready"), ("cond:conveyor/ready", "observed_by", "conveyor/Status/Busy")])
    add("conveyor.md", "conveyor-alarms", "The low air pressure alarm of the Loop Conveyor stops the Assembly Cell, and its motor trip alarm stops the Camera Quality Cell. The ResetAlarms method clears both alarms after the guard is closed. Call the line supervisor if an alarm returns twice in one shift.", [
        ("alarm:conveyor/NoAirPressure", "stops", "assembly"), ("alarm:conveyor/MotorTrip", "stops", "qc")])
    add("warehouse.md", "warehouse-operations", "The Vertical Warehouse serves bay 5. ExtractTray requires the warehouse to be idle; the Busy flag in the Status folder tells the controller when that condition holds. The method moves a tray to the operator bay. SendBack also moves a tray. Wait ten seconds after the lift stops before opening the bay door.", [
        ("warehouse", "serves_bay", "bay:5"), ("warehouse/ExtractTray", "requires", "cond:warehouse/idle"), ("cond:warehouse/idle", "observed_by", "warehouse/Status/Busy"), ("warehouse", "moves", "item:tray")])
    add("warehouse.md", "warehouse-reset", "The warehouse alarm reset uses ResetAlarms. Its operation needs the stock-ready condition; the StockReady flag in Inventory tells the operator when it holds, and the method returns a completion flag. The operator must check that no person is inside the lift before starting a tray cycle.", [
        ("warehouse/ResetAlarms", "requires", "cond:warehouse/stock-ready"), ("cond:warehouse/stock-ready", "observed_by", "warehouse/Inventory/StockReady")])
    add("rovers.md", "rovers-missions", "Rover R-1, also called the first rover, serves bay 5 and moves a board from the warehouse to pallet 7. StartMission requires the rover to be idle; the Busy flag in the Status folder of R-1 reports that condition. Rover R-2 serves bay 5 too, but it does not serve bay 3. Charge either rover for twenty minutes after four missions.", [
        ("rover1", "serves_bay", "bay:5"), ("rover1", "moves", "item:board"), ("rover1/Motion/StartMission", "requires", "cond:rover/idle"), ("cond:rover/idle", "observed_by", "rover1/Status/Busy"), ("rover2", "serves_bay", "bay:5")])
    add("rovers.md", "rovers-confirm", "The delivery mission is confirmed by the LastResult flag in the Status folder of R-1. The second rover, also called R-2, can move a cover to pallet 7. It then waits for bay 5 before returning to the charging point. Do not swap the two mission names in the supervisor configuration.", [
        ("rover1/Status/LastResult", "confirms", "mission:rover/deliver-board"), ("rover2", "moves", "item:cover")])
    add("tester.md", "tester-route", "The Board Tester serves bay 2 and moves a board to the Engraving Cell. BoardIn requires the tester to be ready; the Busy flag in its Status folder reports that condition. The input clamp takes six seconds to close and must be empty before a new board arrives.", [
        ("tester", "serves_bay", "bay:2"), ("tester", "moves", "item:board"), ("tester/Boards/BoardIn", "requires", "cond:tester/ready"), ("cond:tester/ready", "observed_by", "tester/Status/Busy")])
    add("tester.md", "tester-result", "The board test mission is confirmed by the TestPassed flag in the Boards folder. RunTest returns a submitted result before the measurements finish. A failed test keeps the board at the output station until a technician records the reason.", [
        ("tester/Boards/TestPassed", "confirms", "mission:tester/board-test")])
    add("cnc.md", "cnc-route", "The Engraving Cell serves bay 3 and moves a board. PickBoard requires the CNC cell to be idle; the Busy flag in its Status folder reports that condition. The arm must approach from the marked side, and the spindle needs a thirty-second warm-up before engraving.", [
        ("cnc", "serves_bay", "bay:3"), ("cnc", "moves", "item:board"), ("cnc/Arm/PickBoard", "requires", "cond:cnc/idle"), ("cond:cnc/idle", "observed_by", "cnc/Status/Busy")])
    add("cnc.md", "cnc-confirm", "The engraving mission is confirmed by the LastResult flag in the Status folder of the Engraving Cell. PlaceBoard moves the board to pallet 7. Inspect the engraving depth every fifty boards and stop the cell if the depth is outside the work instruction.", [
        ("cnc/Status/LastResult", "confirms", "mission:cnc/engrave-board"), ("cnc", "moves", "item:board")])
    add("assembly.md", "assembly-route", "The Assembly Cell serves bay 4 and moves a top cover and a bottom cover onto pallet 7. Assemble requires the cell to be idle; the Busy flag in its Status folder reports that condition. The two arms must report home before the pallet enters the fixture.", [
        ("assembly", "serves_bay", "bay:4"), ("assembly", "moves", "item:cover-top"), ("assembly", "moves", "item:cover-bottom"), ("assembly/Assembly/Assemble", "requires", "cond:assembly/idle"), ("cond:assembly/idle", "observed_by", "assembly/Status/Busy")])
    add("assembly.md", "assembly-confirm", "The assembly mission is confirmed by the LastResult flag in the Status folder. Screw requires the screwdriver to be ready; the Busy flag changes while the program runs. Replace the bit after two hundred cycles and record the program number in the shift log.", [
        ("assembly/Status/LastResult", "confirms", "mission:assembly/fit-covers"), ("assembly/Assembly/Screw", "requires", "cond:assembly/screwdriver-ready"), ("cond:assembly/screwdriver-ready", "observed_by", "assembly/Status/Busy")])
    add("qc.md", "qc-route", "The Camera Quality Cell serves bay 5. CheckPallet requires the inspection cell to be idle; the Busy flag in its Status folder reports that condition. The method confirms the pallet inspection through the Passed flag in Inspection. The camera takes twelve seconds to scan one pallet.", [
        ("qc", "serves_bay", "bay:5"), ("qc/Inspection/CheckPallet", "requires", "cond:qc/idle"), ("cond:qc/idle", "observed_by", "qc/Status/Busy"), ("qc/Inspection/Passed", "confirms", "mission:qc/inspect-pallet")])
    add("qc.md", "qc-result", "The pallet inspection is confirmed by the Passed flag in the Inspection folder. The camera cell moves the board to the finished pallet record. If the result is false, keep the pallet in bay 5 and ask quality staff to review the images before releasing it.", [
        ("qc/Inspection/Passed", "confirms", "mission:qc/inspect-pallet"), ("qc", "moves", "item:board")])
    add("line.md", "line-route", "The route is bay 1, then bay 2, bay 3, bay 4, and bay 5. The conveyor hands the pallet to bay 2; bay 2 hands it to bay 3; bay 3 hands it to bay 4; bay 4 hands it to bay 5. A pallet must not skip a bay because the barcode reader checks the route at every stop.", [
        ("bay:1", "next_step", "bay:2"), ("bay:2", "next_step", "bay:3"), ("bay:3", "next_step", "bay:4"), ("bay:4", "next_step", "bay:5")])
    add("line.md", "line-stops", "An emergency stop in the Assembly Cell stops the conveyor. An emergency stop on the conveyor stops the warehouse. The low air pressure alarm of the conveyor stops the Assembly Cell. The alarm lamp stays on until the cause is removed and the reset method is accepted.", [
        ("alarm:assembly/EmergencyStop", "stops", "conveyor"), ("alarm:conveyor/EmergencyStop", "stops", "warehouse"), ("alarm:conveyor/NoAirPressure", "stops", "assembly")])
    add("incidents.md", "incident-rover-alias", "On 4 March, the first rover raised an RFID reader fault on the loop conveyor while moving a board. Rover R-1 was the affected unit, and StopMission on that rover fixed the interruption before the pallet was returned.", [
        ("incident:2026-03-04-1", "incident_on", "rover1"), ("incident:2026-03-04-1", "raised", "alarm:conveyor/RFIDFault"), ("incident:2026-03-04-1", "fixed_by_method", "rover1/Motion/StopMission")])
    add("incidents.md", "incident-rover-second", "On 5 March, R-2 reported a screwdriver fault in the Assembly Cell. The second rover was the affected unit, and StopMission on that rover fixed the interruption after the operator checked the fixture.", [
        ("incident:2026-03-05-1", "incident_on", "rover2"), ("incident:2026-03-05-1", "raised", "alarm:assembly/ScrewdriverFault"), ("incident:2026-03-05-1", "fixed_by_method", "rover2/Motion/StopMission")])
    add("incidents.md", "incident-ambiguous", "On 6 March during the night shift, the rover raised a motor trip alarm on the conveyor. The operator stopped the line, moved the pallet to a safe position, and recorded the event for the morning review. The log names no rover, so the supervisor checked both transport units before the next mission was released.", [
        ("incident:2026-03-06-1", "raised", "alarm:conveyor/MotorTrip")])

    # These are short operator and integrator notes.  Most carry one extra
    # link; the four explicit distractors carry none but contain useful values.
    add("conveyor.md", "conveyor-return-bays", "During a maintenance return, the Loop Conveyor handles bay 3 and bay 4. Pallet 8 is used for the empty-fixture check. The return operator reads the belt speed twice before releasing the pallet. A guard reset does not start motion by itself, and the supervisor must authorise the next cycle.", [
        ("conveyor", "serves_bay", "bay:3"), ("conveyor", "serves_bay", "bay:4"), ("conveyor", "moves", "pallet:8")])
    add("warehouse.md", "warehouse-replenishment", "A replenishment tray enters the Vertical Warehouse through bay 1. The operator checks the tray label, closes the lift door, and waits for the position display to settle. The warehouse can hold ten trays. A missing label is a stock problem, not a motion fault, so the operator records it before calling maintenance.", [
        ("warehouse", "serves_bay", "bay:1")])
    add("rovers.md", "rover1-return-route", "R-1 can collect a spare tray from the warehouse and return it to bay 1. It leaves the charging point only after the safety scanner is clear. The supervisor checks the mission name against the pallet label. If the scanner stays blocked, the rover waits; it does not push the pallet or enter the inspection cell.", [
        ("rover1", "moves", "item:tray"), ("rover1", "serves_bay", "bay:1")])
    add("rovers.md", "rover2-fixture-route", "R-2 carries a board to the fixture station at bay 4 during a recovery cycle. The operator confirms the fixture is empty before sending the rover. A second trip is allowed only after the first result is recorded. The recovery route returns through bay 4 before the pallet rejoins production.", [
        ("rover2", "moves", "item:board"), ("rover2", "serves_bay", "bay:4")])
    add("tester.md", "tester-fixture-return", "The Board Tester uses bay 3 for a fixture return. A technician removes the reference board, checks its serial number, and closes the clamp. The test recipe has a five-second settle time and a twenty-second measurement window. A board with a missing serial stays at the input station until the record is corrected.", [
        ("tester", "serves_bay", "bay:3")])
    add("cnc.md", "cnc-recovery-route", "The Engraving Cell can receive a recovery board at bay 2. The arm waits at its marked pose while the operator checks the spindle guard. Engraving a recovery board uses the same serial rule as normal production, but the result is recorded in a separate shift note. The cell must be empty before the next pallet arrives.", [
        ("cnc", "serves_bay", "bay:2")])
    add("assembly.md", "assembly-rework-route", "A rework pallet may return to bay 5 beside the Assembly Cell. The operator removes the top cover before opening the fixture. The screwdriver program is selected from the job card, and the two arms remain in their home poses during the check. Rework parts are counted separately from first-pass parts.", [
        ("assembly", "serves_bay", "bay:5")])
    add("qc.md", "qc-recheck-route", "The Camera Quality Cell can recheck a pallet at bay 4. The quality operator cleans the lens, confirms the lighting reference, and repeats the inspection once. A second failure sends the pallet to manual review. The image archive keeps the serial number and the shift name, but it does not change the production route.", [
        ("qc", "serves_bay", "bay:4")])
    add("conveyor.md", "conveyor-distractor", "The Loop Conveyor uses a nominal speed of 18 metres per minute and a two-second pause at each stop. The drive cabinet is inspected at the start of every shift. A loose cover can cause vibration without raising an alarm. The operator records the sound and calls maintenance if it continues after cleaning.", [])
    add("warehouse.md", "warehouse-distractor", "The Vertical Warehouse checks tray height before a lift cycle. The normal lift time is forty seconds, and the operator bay light remains on for ten seconds after arrival. Keep hands outside the shutter. A tray that feels unusually heavy is isolated for a stock check rather than forced into position.", [])
    add("tester.md", "tester-distractor", "The Board Tester stores a result for thirty days. Its reference board is checked at the start of each morning shift and replaced after one hundred cycles. The test operator wears an antistatic strap. A clean clamp improves repeatability, but cleaning never replaces the scheduled calibration.", [])
    add("qc.md", "qc-distractor", "The Camera Quality Cell uses two lights and one fixed lens. The reference image is renewed every Monday or after a lens change. Keep reflective tools outside the field of view. A clean image does not prove that a pallet passed; the operator must read the recorded result and follow the review rule.", [])
    add("line.md", "line-alternatives", "The Loop Conveyor moves pallet 8 during a return cycle. R-1 moves a tray to bay 1, while R-2 moves a board to bay 4. The Board Tester moves a cover during a fixture check. The operator records the return reason before the pallet enters the next bay.", [
        ("conveyor", "moves", "pallet:8"), ("rover1", "moves", "item:tray"), ("rover2", "moves", "item:board"), ("tester", "moves", "item:cover")])
    add("line.md", "line-alternatives-finish", "The Engraving Cell moves a top cover during a recovery job. The Assembly Cell moves a board into its fixture, and the Camera Quality Cell moves a cover after inspection. Each movement is recorded against the pallet number. A recovery route may return to bay 4, but it must rejoin the normal route before quality inspection.", [
        ("cnc", "moves", "item:cover-top"), ("assembly", "moves", "item:board"), ("qc", "moves", "item:cover")])

    extra_incidents = [
        ("2026-03-07-1", "7 March", "the warehouse operator", "Vertical Warehouse", "warehouse", "a low air pressure alarm", "warehouse/ResetAlarms", "ResetAlarms"),
        ("2026-03-08-1", "8 March", "the first rover", "Rover R-1", "rover1", "a motor trip alarm on the conveyor", "rover1/Motion/StopMission", "StopMission"),
        ("2026-03-09-1", "9 March", "R-2", "Rover R-2", "rover2", "an emergency stop alarm", "rover2/Motion/StopMission", "StopMission"),
        ("2026-03-10-1", "10 March", "the test operator", "Board Tester", "tester", "a low air pressure alarm", "tester/Boards/BoardOut", "BoardOut"),
        ("2026-03-11-1", "11 March", "the CNC operator", "Engraving Cell", "cnc", "an emergency stop alarm", "cnc/Arm/PlaceBoard", "PlaceBoard"),
        ("2026-03-12-1", "12 March", "the assembly operator", "Assembly Cell", "assembly", "a screwdriver fault alarm", "assembly/ResetAlarms", "ResetAlarms"),
        ("2026-03-13-1", "13 March", "the quality operator", "Camera Quality Cell", "qc", "a motor trip alarm on the conveyor", "qc/Inspection/CheckPallet", "CheckPallet"),
        ("2026-03-14-1", "14 March", "the warehouse operator", "Vertical Warehouse", "warehouse", "an emergency stop alarm", "warehouse/ResetAlarms", "ResetAlarms"),
        ("2026-03-15-1", "15 March", "the first rover", "Rover R-1", "rover1", "a low air pressure alarm", "rover1/Motion/StopMission", "StopMission"),
        ("2026-03-16-1", "16 March", "R-2", "Rover R-2", "rover2", "an RFID reader fault", "rover2/Motion/StopMission", "StopMission"),
        ("2026-03-17-1", "17 March", "the test operator", "Board Tester", "tester", "an emergency stop alarm", "tester/Boards/BoardOut", "BoardOut"),
        ("2026-03-18-1", "18 March", "the CNC operator", "Engraving Cell", "cnc", "a motor trip alarm on the conveyor", "cnc/Arm/PlaceBoard", "PlaceBoard"),
        ("2026-03-19-1", "19 March", "the assembly operator", "Assembly Cell", "assembly", "an emergency stop alarm", "assembly/ResetAlarms", "ResetAlarms"),
        ("2026-03-20-1", "20 March", "the quality operator", "Camera Quality Cell", "qc", "a low air pressure alarm", "qc/Inspection/CheckPallet", "CheckPallet"),
        ("2026-03-21-1", "21 March", "the warehouse operator", "Vertical Warehouse", "warehouse", "a motor trip alarm on the conveyor", "warehouse/ResetAlarms", "ResetAlarms"),
        ("2026-03-22-1", "22 March", "the first rover", "Rover R-1", "rover1", "an RFID reader fault", "rover1/Motion/StopMission", "StopMission"),
        ("2026-03-23-1", "23 March", "R-2", "Rover R-2", "rover2", "a low air pressure alarm", "rover2/Motion/StopMission", "StopMission"),
    ]
    alarm_for = {
        "a low air pressure alarm": "NoAirPressure", "an emergency stop alarm": "EmergencyStop",
        "a motor trip alarm on the conveyor": "MotorTrip", "an RFID reader fault": "RFIDFault",
        "a screwdriver fault alarm": "ScrewdriverFault",
    }
    for number, (incident_id, date, actor, display_name, device, alarm_text, fixed_method, method_name) in enumerate(extra_incidents):
        chunk = f"incident-{incident_id}"
        if number % 3 == 0:
            text = f"On {date}, {actor} reported {alarm_text} during pallet run {number + 1}. The technician checked the area and sent {method_name} to {display_name}. The supervisor recorded the affected pallet and returned the line to service after a {number + 2}-minute check."
        elif number % 3 == 1:
            text = f"The line returned to service after {method_name} stopped equipment for case {number + 1}. On {date}, {display_name} had reported {alarm_text}, and {actor} checked the guard before restarting. The shift record names the pallet, the response time, and the follow-up inspection for shift {number + 1}."
        else:
            text = f"During the {date} handover, {actor} described {alarm_text} on {display_name}. The technician isolated area {number + 1}, used {method_name}, and checked the next pallet by hand. No product was released until the supervisor signed follow-up record {number + 1}."
        alarm_device = "assembly" if alarm_text == "a screwdriver fault alarm" else "conveyor" if "conveyor" in alarm_text or "RFID" in alarm_text else device
        add("incidents.md", chunk, text, [
            (f"incident:{incident_id}", "incident_on", device),
            (f"incident:{incident_id}", "raised", f"alarm:{alarm_device}/{alarm_for[alarm_text]}"),
            (f"incident:{incident_id}", "fixed_by_method", fixed_method),
        ])
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
        {"id": "line:main", "type": "Line", "name": "the line", "aliases": [], "props": {}},
    ]
    all_edges: list[dict[str, str]] = []
    cells = {
        "cell:conveyor": "conveyor", "cell:warehouse": "warehouse", "cell:transport": "transport",
        "cell:test": "test", "cell:cnc": "cnc", "cell:assembly": "assembly", "cell:qc": "qc",
    }
    for cell_id, name in cells.items():
        all_nodes.append({"id": cell_id, "type": "Cell", "name": name, "aliases": [], "props": {}})

    model_list = models()
    for model in model_list:
        write_model(model)
    for model in sorted(model_list, key=lambda item: item["device"]):
        nodes, edges = model_graph(model)
        all_nodes.extend(nodes)
        all_edges.extend(edges)

    extra_nodes = [
        ("bay:1", "Bay", "Bay 1"), ("bay:2", "Bay", "Bay 2"), ("bay:3", "Bay", "Bay 3"),
        ("bay:4", "Bay", "Bay 4"), ("bay:5", "Bay", "Bay 5"), ("pallet:7", "Pallet", "Pallet 7"),
        ("pallet:8", "Pallet", "Pallet 8"),
        ("item:board", "Item", "board", ["bare board", "boards"]),
        ("item:cover", "Item", "cover", ["a cover"]),
        ("item:cover-top", "Item", "top cover", ["a top cover"]),
        ("item:cover-bottom", "Item", "bottom cover", ["a bottom cover"]),
        ("item:tray", "Item", "tray", ["a tray", "replenishment tray", "spare tray"]),
    ]
    for entry in extra_nodes:
        node_id, kind, name, *aliases = entry
        all_nodes.append({"id": node_id, "type": kind, "name": name, "aliases": aliases[0] if aliases else [], "props": {}})
    for node_id, kind, name in [
        ("mission:rover/deliver-board", "Mission", "board delivery"), ("mission:tester/board-test", "Mission", "board test mission"),
        ("mission:cnc/engrave-board", "Mission", "engraving mission"), ("mission:assembly/fit-covers", "Mission", "assembly mission"),
        ("mission:qc/inspect-pallet", "Mission", "pallet inspection"),
    ]:
        aliases = {
            "mission:rover/deliver-board": ["delivery mission"],
            "mission:tester/board-test": ["test mission"],
            "mission:cnc/engrave-board": ["engraving job"],
            "mission:assembly/fit-covers": ["fit covers mission"],
            "mission:qc/inspect-pallet": ["pallet inspection mission"],
        }[node_id]
        all_nodes.append({"id": node_id, "type": kind, "name": name, "aliases": aliases, "props": {}})
    conditions = [
        ("cond:conveyor/ready", "line-ready condition", ["line ready"]),
        ("cond:warehouse/idle", "warehouse idle", ["warehouse to be idle", "warehouse is idle"]),
        ("cond:warehouse/stock-ready", "stock-ready condition", ["stock ready"]),
        ("cond:rover/idle", "R-1 idle", ["R-1 is idle", "first rover is idle", "rover to be idle"]),
        ("cond:tester/ready", "tester ready", ["tester to be ready", "tester is ready"]),
        ("cond:cnc/idle", "CNC cell idle", ["CNC cell to be idle", "CNC cell is idle"]),
        ("cond:assembly/idle", "assembly cell idle", ["cell to be idle", "Assembly Cell is idle"]),
        ("cond:assembly/screwdriver-ready", "screwdriver ready", ["screwdriver to be ready", "screwdriver is ready"]),
        ("cond:qc/idle", "inspection cell idle", ["inspection cell to be idle", "inspection cell is idle"]),
    ]
    for node_id, name, aliases in conditions:
        all_nodes.append({"id": node_id, "type": "Condition", "name": name, "aliases": aliases, "props": {}})
    notes, links = prose()
    incident_ids = sorted({edge["s"] for edge in links if edge["s"].startswith("incident:")})
    for incident_id in incident_ids:
        iso_date = incident_id.split(":", 1)[1].rsplit("-", 1)[0]
        parsed_date = calendar_date.fromisoformat(iso_date)
        human_date = f"{parsed_date.day} {parsed_date.strftime('%B')}"
        all_nodes.append({"id": incident_id, "type": "Incident", "name": f"{human_date} incident", "aliases": [human_date], "props": {"date": iso_date}})
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
