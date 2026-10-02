from collections.abc import Callable
from dataclasses import dataclass

from line import Line
from line.machine import REPAIR_S

from .actions import CallPerson, Repair
from .snapshot import Snapshot
from .strategy import Outcome, Strategy
from .symptoms import WINDOW_S, Monitor, Symptom

CHECK_EVERY_S = 60
# A technician needs time to arrive and inspect every machine.
TECHNICIAN_S = 1200


@dataclass
class Incident:
    symptom: Symptom
    outcome: Outcome
    # What was really broken. For the report only: the strategy never sees it.
    truth: list[tuple[str, str]]


class Supervisor:
    """Watches the line, and when code detects a symptom, lets the strategy
    decide and applies its action. The only part that changes the line."""

    def __init__(
        self,
        line: Line,
        monitor: Monitor,
        strategy: Strategy,
        on_symptom: Callable[[int, Symptom], None],
        on_action: Callable[[Outcome], None],
    ) -> None:
        self.line = line
        self.monitor = monitor
        self.strategy = strategy
        self.on_symptom = on_symptom
        self.on_action = on_action
        self.incidents: list[Incident] = []

    def run(self) -> None:
        while not self.line.done:
            self.line.advance(CHECK_EVERY_S)
            symptom = self.monitor.check(self.line.logbook, self.line.t)
            if symptom is not None:
                self.handle(symptom)

    def handle(self, symptom: Symptom) -> None:
        t = self.line.t
        self.on_symptom(len(self.incidents) + 1, symptom)
        snapshot = Snapshot(self.line.machines, self.line.logbook, max(0, t - WINDOW_S), t)
        truth = self.line.active_faults()
        outcome = self.strategy.decide(snapshot, symptom)
        self.on_action(outcome)
        self.apply(outcome, t)
        self.incidents.append(Incident(symptom, outcome, truth))

    def apply(self, outcome: Outcome, t: int) -> None:
        action = outcome.action
        if isinstance(action, Repair):
            self.line.machine(action.machine).repair(action.fault, t)
            self.monitor.reset(t + REPAIR_S)
        elif isinstance(action, CallPerson):
            for machine in self.line.machines:
                machine.repair_all(t, TECHNICIAN_S)
            self.monitor.reset(t + TECHNICIAN_S)
