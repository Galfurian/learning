from ..fault import Fault
from ..machine import Machine
from ..part import Part
from ..signal import Signal


class Misfeed(Fault):
    description = "Parts get stuck in the feeder chute: it needs several attempts per part."
    remedy = "realign the feeder chute"
    slowdown = 1.8

    def affect(self, machine, readings, part):
        readings["retries"] = machine.rng.randint(3, 5)


class EmptyHopper(Fault):
    description = "The hopper is almost out of raw material: parts arrive late."
    remedy = "refill the hopper"
    slowdown = 2.5

    def affect(self, machine, readings, part):
        readings["hopper_kg"] = round(machine.rng.uniform(0.5, 2.0), 1)


class Feeder(Machine):
    kind = "feeder"
    description = "Takes raw parts from the hopper and puts them on the line, one at a time."
    cycle_s = 60
    event = "FEED"
    signals = {"hopper_kg": Signal(20, 50), "retries": Signal(0, 1, decimals=0)}
    faults = [Misfeed, EmptyHopper]

    remaining = 0
    _next_id = 1

    def load(self, count: int) -> None:
        """How many raw parts the hopper holds for this run."""
        self.remaining = count

    def pull(self) -> Part | None:
        if self.remaining == 0:
            return None
        self.remaining -= 1
        part = Part(id=f"P-{self._next_id:03d}")
        self._next_id += 1
        return part
