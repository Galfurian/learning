"""Base class and registry for station types.

To add a station type, create a module in ``factory/stations/``:

    @station("oven")
    class Oven(Station):
        class Params(StationParams):
            bake_s: int

        def step(self, t): ...

and use ``type: oven`` in a recipe. Modules in ``stations/`` are imported
automatically.
"""

import importlib
import pkgutil
import random
from collections import deque
from datetime import datetime
from typing import Any, ClassVar

from pydantic import BaseModel

from .logbook import LogBook
from .part import Part

REGISTRY: dict[str, type["Station"]] = {}


def station(type_name: str):
    """Class decorator: make a station type available to recipes."""

    def decorator(cls: type["Station"]) -> type["Station"]:
        cls.type_name = type_name
        REGISTRY[type_name] = cls
        return cls

    return decorator


def load_station_types() -> dict[str, type["Station"]]:
    """Import every module in ``factory/stations/`` so they can register."""
    package = importlib.import_module(f"{__package__}.stations")
    for module in pkgutil.iter_modules(package.__path__):
        importlib.import_module(f"{package.__name__}.{module.name}")
    return REGISTRY


class StationParams(BaseModel):
    """Parameters every station accepts. Subclass it to add your own."""

    capacity: int = 1


class Station:
    """One machine of the cell.

    The factory calls, every simulated second:

    - ``step(t)``: advance the internal state machine;
    - then it moves finished parts from ``outbox`` to the next station of each
      part's route, when that station ``can_accept()``.
    """

    type_name: ClassVar[str]
    Params: ClassVar[type[StationParams]] = StationParams
    # Fault kinds this station supports, each with its parameter model.
    faults: ClassVar[dict[str, type[BaseModel]]] = {}
    # What each event this station logs means: the station's documentation.
    events: ClassVar[dict[str, str]] = {}

    def __init__(
        self,
        station_id: str,
        params: StationParams,
        logbook: LogBook,
        rng: random.Random,
    ) -> None:
        self.id = station_id
        self.params = params
        self.rng = rng
        self.inbox: deque[Part] = deque()
        self.outbox: deque[Part] = deque()
        self._logbook = logbook
        self._now: datetime | None = None

    # --- called by the factory -------------------------------------------

    def can_accept(self) -> bool:
        return len(self.inbox) + self.load() < self.params.capacity

    def receive(self, part: Part, t: datetime) -> None:
        self.inbox.append(part)

    def step(self, t: datetime) -> None:
        raise NotImplementedError

    def apply_fault(self, kind: str, params: BaseModel, t: datetime) -> None:
        raise NotImplementedError(f"{self.type_name} does not support fault {kind!r}")

    # --- helpers for subclasses -------------------------------------------

    def load(self) -> int:
        """Parts inside the station besides the inbox (being worked on, waiting to leave)."""
        return len(self.outbox)

    def log(self, t: datetime, event: str, part: Part | None = None, **fields: Any) -> None:
        self._logbook.write(t, self.id, event, part.id if part else None, fields)

    @staticmethod
    def every(t: datetime, seconds: int) -> bool:
        """True once every ``seconds`` of the day: handy for periodic telemetry."""
        return (t.hour * 3600 + t.minute * 60 + t.second) % seconds == 0

    def done(self, part: Part, t: datetime) -> None:
        """Hand a finished part to the factory, which moves it on."""
        part.visits.append((self.id, t.strftime("%H%M")))
        self.outbox.append(part)
