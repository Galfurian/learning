from datetime import datetime, timedelta
from enum import Enum

from typing import ClassVar

from pydantic import BaseModel, Field

from ..part import Part
from ..station import Station, StationParams, station


class State(Enum):
    RUNNING = "running"
    JAMMED = "jammed"


class Jam(BaseModel):
    duration_s: int = Field(gt=0)

    # How to recognise this fault in an explanation, for grading.
    keywords: ClassVar[dict[str, tuple[str, ...]]] = {
        "exact": ("jam",),
        "partial": ("conveyor", "belt"),
    }


@station("conveyor")
class Conveyor(Station):
    """Belt conveyor: several parts travel at once; a jam stops all of them."""

    class Params(StationParams):
        capacity: int = 4
        transit_s: int = 45
        speed_m_s: float = 0.25
        telemetry_every_s: int = 300

    faults = {"jam": Jam}
    events = {
        "ENTER": "A part is put on the belt (on_belt: parts now on the belt).",
        "EXIT": "A part reaches the end of the belt.",
        "JAM": "The belt stops: every part on it waits until JAM_CLEARED.",
        "JAM_CLEARED": "The belt runs again.",
        "TELEMETRY": "Periodic speed and motor current.",
    }

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.state = State.RUNNING
        self.jam_until: datetime | None = None
        self.on_belt: list[list] = []  # [part, seconds left]

    def receive(self, part: Part, t: datetime) -> None:
        self.on_belt.append([part, self.params.transit_s])
        self.log(t, "ENTER", part, on_belt=len(self.on_belt))

    def apply_fault(self, kind: str, params: BaseModel, t: datetime) -> None:
        assert isinstance(params, Jam)
        self.state = State.JAMMED
        self.jam_until = t + timedelta(seconds=params.duration_s)
        self.log(t, "JAM", on_belt=len(self.on_belt), motor_current_a=7.9)

    def step(self, t: datetime) -> None:
        p = self.params
        if self.every(t, p.telemetry_every_s):
            speed = p.speed_m_s if self.state is State.RUNNING else 0.0
            self.log(t, "TELEMETRY", speed_m_s=speed, on_belt=len(self.on_belt),
                     motor_current_a=round(2.1 + 0.3 * len(self.on_belt) + self.rng.gauss(0, 0.05), 1))

        if self.state is State.JAMMED:
            if self.jam_until is not None and t >= self.jam_until:
                self.state = State.RUNNING
                self.log(t, "JAM_CLEARED", on_belt=len(self.on_belt))
            return

        for item in self.on_belt:
            item[1] -= 1
        while self.on_belt and self.on_belt[0][1] <= 0 and not self.outbox:
            part, _ = self.on_belt.pop(0)
            self.log(t, "EXIT", part)
            self.done(part, t)

    def load(self) -> int:
        return len(self.on_belt) + len(self.outbox)

    def can_accept(self) -> bool:
        return self.load() < self.params.capacity
