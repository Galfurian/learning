from dataclasses import dataclass

from line import LogBook, LogLine, Machine


@dataclass(frozen=True)
class Snapshot:
    """What the supervisor may look at: the machines and their logs in a time window."""

    machines: list[Machine]
    logbook: LogBook
    start: int
    end: int

    def machine(self, name: str) -> Machine:
        return next(machine for machine in self.machines if machine.name == name)

    def lines(self, name: str) -> list[LogLine]:
        return self.logbook.lines(name, self.start, self.end)
