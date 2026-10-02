"""What the supervisor can do to the line. A strategy proposes one, the
supervisor applies it."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Repair:
    machine: str
    fault: str
    probability: float

    def text(self) -> str:
        return f"repair {self.machine}: {self.fault} (p={self.probability:.2f})"


@dataclass(frozen=True)
class CallPerson:
    reason: str

    def text(self) -> str:
        return f"stop the line and call a technician: {self.reason}"


Action = Repair | CallPerson
