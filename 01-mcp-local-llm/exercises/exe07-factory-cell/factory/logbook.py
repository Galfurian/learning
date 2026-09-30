from datetime import datetime, time
from typing import Any

from pydantic import BaseModel


class LogLine(BaseModel):
    production: str
    t: datetime
    station: str
    event: str
    part: str | None = None
    fields: dict[str, Any] = {}

    def text(self) -> str:
        """One compact line, e.g. ``0952 M1 TOOL_CHANGE tool=T12``."""
        items = [self.t.strftime("%H%M"), self.station, self.event]
        if self.part:
            items.append(f"part={self.part}")
        items += [f"{key}={_fmt(value)}" for key, value in self.fields.items()]
        return " ".join(items)


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:.3f}".rstrip("0").rstrip(".")
    return str(value)


class LogBook:
    """All log lines of a run, grouped by station."""

    def __init__(self) -> None:
        self._lines: list[LogLine] = []
        self.production = ""

    def write(self, t: datetime, station: str, event: str, part: str | None, fields: dict) -> None:
        self._lines.append(
            LogLine(production=self.production, t=t, station=station, event=event,
                    part=part, fields=fields)
        )

    def lines(
        self,
        station: str | None = None,
        production: str | None = None,
        start: time | None = None,
        end: time | None = None,
    ) -> list[LogLine]:
        """Filter by station, production, and time of day (``start <= t < end``)."""
        return [
            line
            for line in self._lines
            if station in (None, line.station)
            and production in (None, line.production)
            and (start is None or line.t.time() >= start)
            and (end is None or line.t.time() < end)
        ]

    def text(self, station: str | None = None, production: str | None = None) -> list[str]:
        return [line.text() for line in self.lines(station, production)]

    def jsonl(self, station: str | None = None, production: str | None = None) -> str:
        return "\n".join(line.model_dump_json() for line in self.lines(station, production))
