"""Detecting that something is wrong is ordinary code: counting, not judging."""

from dataclasses import dataclass

from line import LogBook

WINDOW_S = 600


@dataclass(frozen=True)
class Symptom:
    t: int
    text: str


class Detector:
    """Looks at the last ``WINDOW_S`` seconds of logs and returns a symptom, or None."""

    def check(self, logbook: LogBook, start: int, t: int) -> Symptom | None:
        raise NotImplementedError


class RejectRate(Detector):
    """Too many parts rejected by the final inspection."""

    def __init__(self, machine: str, max_rejects: int = 2) -> None:
        self.machine = machine
        self.max_rejects = max_rejects

    def check(self, logbook, start, t):
        results = [line.fields.get("result") for line in logbook.lines(self.machine, start, t)]
        rejects = results.count("REJECT")
        if rejects > self.max_rejects:
            return Symptom(t, f"{rejects} of the last {len(results)} parts were rejected at final inspection.")
        return None


class LowThroughput(Detector):
    """Fewer parts than expected reached the end of the line."""

    def __init__(self, machine: str, min_parts: int = 7) -> None:
        self.machine = machine
        self.min_parts = min_parts

    def check(self, logbook, start, t):
        if t - start < WINDOW_S:
            return None  # not enough history yet
        parts = len(logbook.lines(self.machine, start, t))
        if parts < self.min_parts:
            minutes = (t - start) // 60
            return Symptom(t, f"Only {parts} parts reached final inspection in the last {minutes} minutes.")
        return None


class Monitor:
    """Runs every detector; after an incident, it starts counting again from zero."""

    def __init__(self, detectors: list[Detector]) -> None:
        self.detectors = detectors
        self.since = 0

    def check(self, logbook: LogBook, t: int) -> Symptom | None:
        start = max(self.since, t - WINDOW_S)
        for detector in self.detectors:
            symptom = detector.check(logbook, start, t)
            if symptom is not None:
                return symptom
        return None

    def reset(self, t: int) -> None:
        self.since = t
