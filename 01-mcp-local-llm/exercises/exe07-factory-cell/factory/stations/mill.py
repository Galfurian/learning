from datetime import datetime, timedelta
from enum import Enum

from typing import ClassVar

from pydantic import BaseModel, Field

from ..part import Part
from ..station import Station, StationParams, station


class State(Enum):
    IDLE = "idle"
    LOADING = "loading"
    CUTTING = "cutting"
    UNLOADING = "unloading"
    TOOL_CHANGE = "tool_change"


class ToolOffsetError(BaseModel):
    """The tool breaks; its replacement gets a wrong length offset, entered by hand.

    Every part cut with that tool is off by ``value_mm``, until the scheduled
    inspection ``duration_s`` later swaps the tool again.
    """

    value_mm: float
    duration_s: int = Field(gt=0)

    # How to recognise this fault in an explanation, for grading: the real cause
    # is the wrong offset of the replacement tool, not the breakage itself.
    keywords: ClassVar[dict[str, tuple[str, ...]]] = {
        "exact": ("offset", "manual", "length"),
        "partial": ("break", "tool change", "replacement tool"),
    }


@station("mill")
class Mill(Station):
    """CNC milling machine with tool wear and tool changes."""

    class Params(StationParams):
        load_s: int = 20
        cycle_s: int = 240
        unload_s: int = 20
        tool_change_s: int = 120
        tool_life_parts: int = 18
        first_tool: int = 7
        telemetry_every_s: int = 120

    faults = {"tool_offset_error": ToolOffsetError}
    events = {
        "LOAD": "A raw part is clamped in the mill.",
        "CUT_START": "Milling starts with the tool currently mounted (tool=T..).",
        "SPINDLE": "Periodic spindle load and temperature while cutting.",
        "CUT_DONE": "Milling finished. parts_on_tool counts the parts cut by this tool.",
        "UNLOAD": "The milled part leaves the mill.",
        "ALARM": "A machine alarm (code, message).",
        "TOOL_CHANGE_START": "The mounted tool is removed. reason=wear_limit (end of life), "
                             "breakage, or scheduled_inspection.",
        "TOOL_CHANGE_DONE": "A new tool is mounted. length_offset_mm is the tool length entered in "
                            "the machine; offset_source=presetter means measured by the "
                            "presetter, manual means typed in by an operator.",
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.state = State.IDLE
        self.part: Part | None = None
        self.until: datetime | None = None
        self.tool = self.params.first_tool
        self.parts_on_tool = 0
        self.offset_error_mm = 0.0
        # Next tool change: (reason, offset error of the new tool, offset source).
        self.pending: tuple[str, float, str] | None = None
        self.inspection_at: datetime | None = None

    def apply_fault(self, kind: str, params: BaseModel, t: datetime) -> None:
        assert isinstance(params, ToolOffsetError)
        self.log(t, "ALARM", code="E214", message="tool breakage suspected", tool=f"T{self.tool}")
        self.pending = ("breakage", params.value_mm, "manual")
        self.inspection_at = t + timedelta(seconds=params.duration_s)

    def step(self, t: datetime) -> None:
        p = self.params
        if self.inspection_at is not None and t >= self.inspection_at:
            self.pending = ("scheduled_inspection", 0.0, "presetter")
            self.inspection_at = None

        if self.state is State.CUTTING and (self.until - t).seconds % p.telemetry_every_s == 0:
            load = (58.0 + 0.4 * self.parts_on_tool + 100 * self.offset_error_mm
                    + self.rng.gauss(0, 1.2))
            self.log(t, "SPINDLE", part=self.part, load_pct=round(load, 1),
                     temp_c=round(41.0 + 0.2 * self.parts_on_tool + self.rng.gauss(0, 0.3), 1))

        if self.state is State.IDLE:
            if self.outbox:
                return
            if self.pending is None and self.parts_on_tool >= p.tool_life_parts:
                self.pending = ("wear_limit", 0.0, "presetter")
            if self.pending is not None:
                self.log(t, "TOOL_CHANGE_START", tool_out=f"T{self.tool}", reason=self.pending[0])
                self._start(t, State.TOOL_CHANGE, p.tool_change_s)
            elif self.inbox:
                self.part = self.inbox.popleft()
                self.log(t, "LOAD", self.part)
                self._start(t, State.LOADING, p.load_s)
            return

        if t < self.until:
            return

        if self.state is State.TOOL_CHANGE:
            reason, error, source = self.pending
            self.tool += 1
            self.parts_on_tool = 0
            self.offset_error_mm = error
            self.pending = None
            self.log(t, "TOOL_CHANGE_DONE", tool_in=f"T{self.tool}",
                     length_offset_mm=round(112.40 + self.rng.gauss(0, 0.01), 3), offset_source=source)
            self.state = State.IDLE

        elif self.state is State.LOADING:
            self.log(t, "CUT_START", self.part, program="O2041", tool=f"T{self.tool}")
            self._start(t, State.CUTTING, p.cycle_s)

        elif self.state is State.CUTTING:
            part = self.part
            part.add(self.id, "process variation", self.rng.gauss(0, 0.006))
            part.add(self.id, "tool wear", 0.001 * self.parts_on_tool)
            if self.offset_error_mm:
                part.add(self.id, "fault:tool_offset_error", self.offset_error_mm)
            self.parts_on_tool += 1
            self.log(t, "CUT_DONE", part, tool=f"T{self.tool}", parts_on_tool=self.parts_on_tool)
            self._start(t, State.UNLOADING, p.unload_s)

        elif self.state is State.UNLOADING:
            self.log(t, "UNLOAD", self.part)
            self.done(self.part, t)
            self.part = None
            self.state = State.IDLE

    def load(self) -> int:
        return len(self.outbox) + (self.part is not None)

    def _start(self, t: datetime, state: State, seconds: int) -> None:
        self.state = state
        self.until = t + timedelta(seconds=seconds)
