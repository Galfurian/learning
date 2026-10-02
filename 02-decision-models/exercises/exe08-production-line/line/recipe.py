from dataclasses import dataclass, field

from .logbook import START_MINUTES


@dataclass(frozen=True)
class FaultAt:
    """Break ``machine`` with fault ``fault`` at military time ``at`` (``"0915"``)."""

    at: str
    machine: str
    fault: str

    @property
    def t(self) -> int:
        minutes = int(self.at[:2]) * 60 + int(self.at[2:])
        return (minutes - START_MINUTES) * 60


@dataclass(frozen=True)
class Recipe:
    """What the line produces, and what goes wrong during the run."""

    parts: int
    faults: list[FaultAt] = field(default_factory=list)
    seed: int = 7
