import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Signal:
    """A value a machine reports every cycle, and its nominal range.

    A healthy machine reads around the middle of the range, with some noise.
    """

    low: float
    high: float
    decimals: int = 1

    @property
    def center(self) -> float:
        return (self.low + self.high) / 2

    @property
    def noise(self) -> float:
        """Standard deviation of a healthy reading."""
        return (self.high - self.low) / 10

    def sample(self, rng: random.Random) -> float | int:
        value = round(rng.gauss(self.center, self.noise), self.decimals)
        return int(value) if self.decimals == 0 else value

    def nominal(self) -> str:
        return f"{self.low:.{self.decimals}f}-{self.high:.{self.decimals}f}"
