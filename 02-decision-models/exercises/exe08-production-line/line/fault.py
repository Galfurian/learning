import re
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from .machine import Machine
    from .part import Part


class Fault:
    """Something wrong inside a machine.

    A concrete fault declares what it is (``description``), how a technician
    fixes it (``remedy``), and overrides ``affect`` to change what the machine
    does and reports. It never logs its own name: the logs only show effects.
    """

    description: ClassVar[str]
    remedy: ClassVar[str]
    # How much longer every cycle takes while the fault is active.
    slowdown: ClassVar[float] = 1.0

    def __init__(self) -> None:
        self.cycles = 0  # cycles completed while active: lets effects grow over time

    @classmethod
    def name(cls) -> str:
        """``BeltSlip`` -> ``belt_slip``."""
        return re.sub(r"(?<!^)(?=[A-Z])", "_", cls.__name__).lower()

    def start(self, machine: "Machine", t: int) -> None:
        """Called once, when the fault appears."""

    def affect(self, machine: "Machine", readings: dict[str, float], part: "Part") -> None:
        """Called at the end of every cycle: change ``readings`` and ``part``."""
