from dataclasses import dataclass
from typing import Literal

NOMINAL_MM = 40.000
TOLERANCE_MM = 0.050

Status = Literal["in_progress", "ok", "rejected"]


@dataclass
class Part:
    id: str
    dimension_mm: float = NOMINAL_MM
    status: Status = "in_progress"
