from datetime import datetime, timedelta
from enum import Enum

from ..part import Part
from ..station import Station, StationParams, station


class State(Enum):
    IDLE = "idle"
    RETRIEVING = "retrieving"
    GAUGING = "gauging"
    STORING = "storing"


@station("warehouse")
class Warehouse(Station):
    """Automatic warehouse: hands out raw parts, gauges and stores finished ones."""

    events = {
        "RETRIEVE_START": "A raw part leaves its storage slot (slot=A-...). Start of the part's route.",
        "RETRIEVE_DONE": "The raw part is handed to the robot.",
        "GAUGE_START": "A finished part is back from the mill and the final gauge starts measuring it.",
        "GAUGE": "Final check of a FINISHED part. measured_mm and deviation_mm from nominal; "
                 "result=OK: within tolerance, stored. result=REJECT: out of tolerance, "
                 "goes to the reject bay.",
        "TO_REJECT_BAY": "A finished part that failed the gauge is set aside.",
        "STORED": "A finished part that passed the gauge is stored (slot=B-...). End of its route.",
        "INVENTORY": "Periodic stock report: stored parts, reject bay, free slots.",
    }

    class Params(StationParams):
        capacity: int = 1000
        retrieve_s: int = 20
        gauge_s: int = 10
        store_s: int = 15
        inventory_every_s: int = 1800

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.state = State.IDLE
        self.part: Part | None = None
        self.until: datetime | None = None
        self.next_slot = 1
        self.stored = 0
        self.rejected = 0

    def step(self, t: datetime) -> None:
        p = self.params
        if self.every(t, p.inventory_every_s):
            self.log(t, "INVENTORY", stored=self.stored, reject_bay=self.rejected,
                     free_slots=200 - self.stored)

        if self.state is State.IDLE and self.inbox:
            self.part = self.inbox.popleft()
            if self.part.is_first_stop:
                self._start(t, State.RETRIEVING, p.retrieve_s)
                self.log(t, "RETRIEVE_START", self.part, slot=f"A-{self.next_slot:03d}")
                self.next_slot += 1
            else:
                self._start(t, State.GAUGING, p.gauge_s)
                self.log(t, "GAUGE_START", self.part)
            return

        if self.until is None or t < self.until:
            return
        part = self.part
        assert part is not None

        if self.state is State.RETRIEVING:
            self.log(t, "RETRIEVE_DONE", part)
            self._finish(part, t)

        elif self.state is State.GAUGING:
            measured = part.dimension_mm + self.rng.gauss(0, 0.002)
            deviation = measured - part.nominal_mm
            ok = abs(deviation) <= part.tolerance_mm
            self.log(t, "GAUGE", part, measured_mm=round(measured, 3),
                     deviation_mm=round(deviation, 3), result="OK" if ok else "REJECT")
            if ok:
                self._start(t, State.STORING, p.store_s)
            else:
                part.status = "rejected"
                self.rejected += 1
                self.log(t, "TO_REJECT_BAY", part)
                self._finish(part, t)

        elif self.state is State.STORING:
            part.status = "stored"
            self.stored += 1
            self.log(t, "STORED", part, slot=f"B-{self.stored:03d}")
            self._finish(part, t)

    def load(self) -> int:
        return len(self.outbox) + (self.part is not None)

    def _start(self, t: datetime, state: State, seconds: int) -> None:
        self.state = state
        self.until = t + timedelta(seconds=seconds)

    def _finish(self, part: Part, t: datetime) -> None:
        self.done(part, t)
        self.state, self.part, self.until = State.IDLE, None, None
