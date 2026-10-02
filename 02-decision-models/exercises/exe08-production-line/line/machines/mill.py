from ..fault import Fault
from ..machine import Machine
from ..part import NOMINAL_MM, TOLERANCE_MM
from ..signal import Signal

ROUTINE_TOOL_CHANGE_EVERY = 25
LENGTH_OFFSET_MM = 112.267


class ToolWear(Fault):
    description = "The cutting tool is worn: spindle load rises slowly and dimensions drift slowly."
    remedy = "replace the cutting tool"

    def affect(self, machine, readings, part):
        readings["spindle_load"] += round(1.5 * self.cycles)
        part.dimension_mm += 0.003 * self.cycles


class WrongOffset(Fault):
    description = (
        "The tool length offset is wrong: dimensions jump by a fixed amount right after "
        "a tool change, while spindle load stays normal."
    )
    remedy = "measure the tool and correct its length offset"

    def start(self, machine, t):
        # A tool change, with the offset typed by hand: 0.120 mm off.
        machine.change_tool(t, LENGTH_OFFSET_MM + 0.120)

    def affect(self, machine, readings, part):
        part.dimension_mm += 0.120


class CoolantLow(Fault):
    description = "Not enough coolant: the temperature keeps rising and dimensions grow with it."
    remedy = "refill the coolant tank"

    def affect(self, machine, readings, part):
        readings["temp_c"] = round(readings["temp_c"] + 1.5 * self.cycles, 1)
        part.dimension_mm += 0.0015 * self.cycles


class Mill(Machine):
    kind = "mill"
    description = "Cuts each part to its final dimension, and probes it inside the machine."
    cycle_s = 50
    event = "CUT"
    signals = {"spindle_load": Signal(55, 70, decimals=0), "temp_c": Signal(30, 40)}
    measures = {"probe_mm": Signal(NOMINAL_MM - TOLERANCE_MM, NOMINAL_MM + TOLERANCE_MM, decimals=3)}
    faults = [ToolWear, WrongOffset, CoolantLow]

    tool = 7
    parts_cut = 0

    def work(self, part, readings, t):
        part.dimension_mm += self.rng.gauss(0, 0.004)
        readings["probe_mm"] = round(part.dimension_mm, 3)
        self.parts_cut += 1
        if self.parts_cut % ROUTINE_TOOL_CHANGE_EVERY == 0:
            self.change_tool(t, LENGTH_OFFSET_MM)

    def change_tool(self, t: int, length_offset_mm: float) -> None:
        self.tool += 1
        self.log(t, "TOOL_CHANGE", tool_in=f"T{self.tool}", length_offset_mm=round(length_offset_mm, 3))
