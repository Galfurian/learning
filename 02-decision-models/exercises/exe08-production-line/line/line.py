import random

from .logbook import LogBook
from .machine import Machine
from .machines.feeder import Feeder
from .part import Part
from .recipe import Recipe

MachineSpec = tuple[str, type[Machine]]


class Line:
    """Machines in series and a clock. Every second it lets each machine work,
    then moves finished parts one step down the line."""

    def __init__(self, layout: list[MachineSpec], recipe: Recipe) -> None:
        self.recipe = recipe
        self.logbook = LogBook()
        self.t = 0
        self.finished: list[Part] = []
        self.machines = [
            cls(name, self.logbook, random.Random(f"{recipe.seed}-{name}")) for name, cls in layout
        ]
        first = self.machines[0]
        if not isinstance(first, Feeder):
            raise TypeError("the first machine of a line must be a Feeder")
        first.load(recipe.parts)
        self._pending = sorted(recipe.faults, key=lambda fault: fault.t)
        for fault in self._pending:
            self.machine(fault.machine).fault_class(fault.fault)  # fail early on typos

    def machine(self, name: str) -> Machine:
        for machine in self.machines:
            if machine.name == name:
                return machine
        raise ValueError(f"no machine {name!r}. Machines: {[m.name for m in self.machines]}")

    @property
    def done(self) -> bool:
        return len(self.finished) == self.recipe.parts

    def advance(self, seconds: int) -> None:
        for _ in range(seconds):
            if self.done:
                return
            self.t += 1
            self._inject_due_faults()
            for machine in self.machines:
                machine.tick(self.t)
            self._move_parts()

    def _inject_due_faults(self) -> None:
        while self._pending and self._pending[0].t <= self.t:
            fault = self._pending.pop(0)
            self.machine(fault.machine).inject(fault.fault, self.t)

    def _move_parts(self) -> None:
        last = self.machines[-1]
        part = last.take()
        if part is not None:
            self.finished.append(part)
        for upstream, downstream in reversed(list(zip(self.machines, self.machines[1:]))):
            if downstream.can_accept():
                part = upstream.take()
                if part is not None:
                    downstream.accept(part)

    def active_faults(self) -> list[tuple[str, str]]:
        """The truth: which faults are active now. Only the final report reads it."""
        return [(machine.name, fault.name()) for machine in self.machines for fault in machine.active]
