from typing import Literal

from pydantic import BaseModel

Status = Literal["in_progress", "stored", "rejected", "scrapped"]


class Contribution(BaseModel):
    """Something that changed the part's dimension, and why."""

    station: str
    cause: str
    delta_mm: float


class Part(BaseModel):
    id: str
    production: str
    route: list[str]
    nominal_mm: float
    tolerance_mm: float
    stop: int = 0
    status: Status = "in_progress"
    contributions: list[Contribution] = []
    visits: list[tuple[str, str]] = []

    @property
    def station(self) -> str:
        return self.route[self.stop]

    @property
    def is_first_stop(self) -> bool:
        return self.stop == 0

    @property
    def is_last_stop(self) -> bool:
        return self.stop == len(self.route) - 1

    @property
    def dimension_mm(self) -> float:
        return self.nominal_mm + sum(c.delta_mm for c in self.contributions)

    def add(self, station: str, cause: str, delta_mm: float) -> None:
        self.contributions.append(Contribution(station=station, cause=cause, delta_mm=delta_mm))
