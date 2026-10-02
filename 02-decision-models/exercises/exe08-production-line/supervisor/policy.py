"""When the probabilities are good enough to act. Ordinary code, no model."""

from dataclasses import dataclass
from typing import Any

from .questions import NONE


@dataclass(frozen=True)
class Policy:
    # Step 1: look at machines down to this probability, at most this many.
    min_machine_p: float = 0.10
    max_candidates: int = 2
    # Step 2: repair only when the fault is at least this likely.
    min_fault_p: float = 0.60

    def candidates(self, answer: dict[str, Any]) -> list[str]:
        ranked = sorted(answer["probabilities"].items(), key=lambda item: -item[1])
        return [name for name, p in ranked if p >= self.min_machine_p][: self.max_candidates]

    def fault(self, answer: dict[str, Any]) -> str | None:
        """The fault to repair, or None: the machine looks fine, or the model is unsure."""
        choice = answer["choice"]
        if choice == NONE or answer["probabilities"][choice] < self.min_fault_p:
            return None
        return choice
