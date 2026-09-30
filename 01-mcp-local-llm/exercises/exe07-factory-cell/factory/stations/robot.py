from datetime import datetime, timedelta
from enum import Enum

from ..part import Part
from ..station import Station, StationParams, station


class State(Enum):
    IDLE = "idle"
    MOVE_TO_PICK = "move_to_pick"
    MOVE_TO_PLACE = "move_to_place"


@station("robot")
class Robot(Station):
    """Pick-and-place robot. It can serve several legs of the route."""

    events = {
        "PICK": "The robot grips a part at the station named by source (grip_force_n).",
        "PLACE": "The robot puts the part down at the station named by target.",
    }

    class Params(StationParams):
        move_s: int = 6
        grip_s: int = 3

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.state = State.IDLE
        self.part: Part | None = None
        self.until: datetime | None = None

    def step(self, t: datetime) -> None:
        p = self.params
        if self.state is State.IDLE:
            if self.inbox and not self.outbox:
                self.part = self.inbox.popleft()
                self.state = State.MOVE_TO_PICK
                self.until = t + timedelta(seconds=p.move_s)
            return

        if self.until is None or t < self.until:
            return
        part = self.part
        assert part is not None

        if self.state is State.MOVE_TO_PICK:
            force = round(42.0 + self.rng.gauss(0, 1.5), 1)
            self.log(t, "PICK", part, source=part.route[part.stop - 1], grip_force_n=force)
            self.state = State.MOVE_TO_PLACE
            self.until = t + timedelta(seconds=p.grip_s + p.move_s)

        elif self.state is State.MOVE_TO_PLACE:
            self.log(t, "PLACE", part, target=part.route[part.stop + 1])
            self.done(part, t)
            self.state, self.part, self.until = State.IDLE, None, None

    def load(self) -> int:
        return len(self.outbox) + (self.part is not None)
