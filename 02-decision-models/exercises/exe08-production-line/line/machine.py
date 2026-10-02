import random
from typing import Any, ClassVar

from .fault import Fault
from .logbook import LogBook, LogLine
from .part import Part
from .signal import Signal

# How long a technician keeps a machine stopped to apply a remedy.
REPAIR_S = 300


class Machine:
    """One station of the line: it takes a part, works on it, and hands it on.

    The base class does the whole cycle. A concrete machine only declares:

    - ``kind`` and ``description``: what it is, in words;
    - ``cycle_s``: how long one part takes when healthy;
    - ``event``: the name of the line it logs at the end of every cycle;
    - ``signals``: what it reports every cycle, with nominal ranges;
    - ``measures``: what it measures on the part, if anything;
    - ``faults``: the faults it can have;

    and, if it changes or judges the part, overrides ``work``.
    """

    kind: ClassVar[str]
    description: ClassVar[str]
    cycle_s: ClassVar[int]
    event: ClassVar[str] = "CYCLE"
    signals: ClassVar[dict[str, Signal]] = {}
    # Values the machine measures on the part itself, with their nominal range.
    measures: ClassVar[dict[str, Signal]] = {}
    faults: ClassVar[list[type[Fault]]] = []

    def __init__(self, name: str, logbook: LogBook, rng: random.Random) -> None:
        self.name = name
        self.rng = rng
        self.active: list[Fault] = []
        self._logbook = logbook
        self._inbox: Part | None = None   # input: handed over by the line
        self._part: Part | None = None    # the part being worked on
        self._outbox: Part | None = None  # output: waiting for the next machine
        self._elapsed = 0.0
        self._cycle_time = 0.0
        self._down_until = 0

    @classmethod
    def telemetry(cls) -> dict[str, Signal]:
        """Every numeric value in this machine's cycle line, with its nominal range."""
        cycle = Signal(round(cls.cycle_s * 0.9), round(cls.cycle_s * 1.1), decimals=0)
        return {"cycle_s": cycle} | cls.signals | cls.measures

    # --- input and output: used by the line ---------------------------------

    def can_accept(self) -> bool:
        return self._inbox is None

    def accept(self, part: Part) -> None:
        self._inbox = part

    def take(self) -> Part | None:
        part, self._outbox = self._outbox, None
        return part

    # --- the work cycle -------------------------------------------------------

    def tick(self, t: int) -> None:
        """Advance one second."""
        if t < self._down_until or self._outbox is not None:
            return
        if self._part is None:
            self._part = self.pull()
            if self._part is None:
                return
            self._elapsed = 0.0
            self._cycle_time = self.cycle_s * self.slowdown() * self.rng.uniform(0.95, 1.05)
        self._elapsed += 1
        if self._elapsed >= self._cycle_time:
            self._finish(t)

    def pull(self) -> Part | None:
        """The next part to work on. The first machine of a line overrides it."""
        part, self._inbox = self._inbox, None
        return part

    def work(self, part: Part, readings: dict[str, Any], t: int) -> None:
        """What the machine does to the part. Default: nothing, it only moves it."""

    def _finish(self, t: int) -> None:
        part = self._part
        assert part is not None
        readings: dict[str, Any] = {"cycle_s": round(self._cycle_time)}
        readings |= {name: signal.sample(self.rng) for name, signal in self.signals.items()}
        for fault in self.active:
            fault.affect(self, readings, part)
            fault.cycles += 1
        self.work(part, readings, t)
        self.log(t, self.event, part, **readings)
        self._part, self._outbox = None, part

    def slowdown(self) -> float:
        factor = 1.0
        for fault in self.active:
            factor *= fault.slowdown
        return factor

    # --- faults and repairs -----------------------------------------------------

    @classmethod
    def fault_class(cls, name: str) -> type[Fault]:
        for fault in cls.faults:
            if fault.name() == name:
                return fault
        raise ValueError(f"{cls.kind} has no fault {name!r}. Known: {[f.name() for f in cls.faults]}")

    def inject(self, name: str, t: int) -> None:
        fault = self.fault_class(name)()
        self.active.append(fault)
        fault.start(self, t)

    def repair(self, name: str, t: int) -> None:
        """Apply the remedy of fault ``name``. It only helps if that fault is really there."""
        remedy = self.fault_class(name).remedy
        self.log(t, "MAINTENANCE", action=remedy.replace(" ", "_"))
        self.active = [fault for fault in self.active if fault.name() != name]
        self._down_until = t + REPAIR_S

    def repair_all(self, t: int, down_s: int = REPAIR_S) -> None:
        """A person inspects the machine and fixes whatever is wrong."""
        if self.active:
            self.log(t, "MAINTENANCE", action="full_inspection")
        self.active = []
        self._down_until = t + down_s

    # --- logging ----------------------------------------------------------------

    def log(self, t: int, event: str, part: Part | None = None, **fields: Any) -> None:
        self._logbook.write(LogLine(t, self.name, event, part.id if part else None, fields))
