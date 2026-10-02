from dataclasses import dataclass, field
from typing import Any

START_MINUTES = 8 * 60  # the line starts at 08:00


def hhmm(t: int) -> str:
    """Seconds since the start of the shift, as military time: 3120 -> '0852'."""
    minutes = START_MINUTES + t // 60
    return f"{minutes // 60 % 24:02d}{minutes % 60:02d}"


@dataclass
class LogLine:
    t: int
    machine: str
    event: str
    part: str | None = None
    fields: dict[str, Any] = field(default_factory=dict)

    def text(self) -> str:
        """One compact line, for example ``0852 C1 TRANSIT part=P-012 cycle_s=46 motor_a=4.1``."""
        items = [hhmm(self.t), self.machine, self.event]
        if self.part:
            items.append(f"part={self.part}")
        items += [f"{key}={value}" for key, value in self.fields.items()]
        return " ".join(items)


class LogBook:
    """Every log line of the run, in time order."""

    def __init__(self) -> None:
        self._lines: list[LogLine] = []

    def write(self, line: LogLine) -> None:
        self._lines.append(line)

    def lines(self, machine: str | None = None, start: int = 0, end: int | None = None) -> list[LogLine]:
        """Lines of ``machine`` (or of every machine) with ``start <= t <= end``."""
        return [
            line
            for line in self._lines
            if machine in (None, line.machine) and line.t >= start and (end is None or line.t <= end)
        ]
