from datetime import datetime, timedelta
from enum import Enum

from ..part import Part
from ..station import Station, StationParams, station


class State(Enum):
    IDLE = "idle"
    INSPECTING = "inspecting"


@station("vision_qc")
class VisionQC(Station):
    """Camera inspection of raw parts: surface and orientation."""

    events = {
        "INSPECT": "Camera check of a RAW part, before milling. surface=OK and result=ACCEPT: "
                   "goes on to the mill. surface=SCRATCH and result=REJECT: scrapped here, "
                   "it never reaches the mill nor the final gauge.",
        "TO_SCRAP_BIN": "A raw part rejected by the camera is thrown away.",
        "CAMERA_STATUS": "Periodic camera exposure and sensor temperature.",
    }

    class Params(StationParams):
        inspect_s: int = 8
        defect_rate: float = 0.04
        status_every_s: int = 1800

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.state = State.IDLE
        self.part: Part | None = None
        self.until: datetime | None = None

    def step(self, t: datetime) -> None:
        p = self.params
        if self.every(t, p.status_every_s):
            self.log(t, "CAMERA_STATUS", exposure_ms=round(4.0 + self.rng.gauss(0, 0.1), 1),
                     sensor_temp_c=round(38.0 + self.rng.gauss(0, 0.4), 1))

        if self.state is State.IDLE:
            if self.inbox and not self.outbox:
                self.part = self.inbox.popleft()
                self.state = State.INSPECTING
                self.until = t + timedelta(seconds=p.inspect_s)
            return

        if self.until is None or t < self.until:
            return
        part = self.part
        assert part is not None

        defect = self.rng.random() < p.defect_rate
        score = self.rng.uniform(0.55, 0.75) if defect else self.rng.uniform(0.93, 0.99)
        self.log(t, "INSPECT", part, orientation_deg=round(self.rng.gauss(0, 0.4), 1),
                 surface="SCRATCH" if defect else "OK", score=round(score, 2),
                 result="REJECT" if defect else "ACCEPT")
        if defect:
            part.status = "scrapped"
            self.log(t, "TO_SCRAP_BIN", part)
        self.done(part, t)
        self.state, self.part, self.until = State.IDLE, None, None

    def load(self) -> int:
        return len(self.outbox) + (self.part is not None)
