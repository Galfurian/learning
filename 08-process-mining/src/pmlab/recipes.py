"""Recipes: the operations of an order and the low-level evidence of each."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

UNIT_ROOT = Path(__file__).parents[2]
RECIPES = UNIT_ROOT / "src" / "pmlab" / "data" / "recipes.yaml"


@dataclass(frozen=True)
class Step:
    activity: str
    resource: str
    attrs: dict[str, Any]


@dataclass(frozen=True)
class Operation:
    name: str
    sequence: int
    nominal_s: float
    min_s: float
    resources: dict[str, int]
    depends: tuple[str, ...]
    branch: str
    evidence: tuple[Step, ...]


@dataclass(frozen=True)
class Recipe:
    name: str
    operations: tuple[Operation, ...]


def load_recipes(path: Path = RECIPES) -> dict[str, Recipe]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    recipes = {}
    for name, body in data["recipes"].items():
        operations = tuple(
            Operation(
                name=op["name"],
                sequence=int(op["sequence"]),
                nominal_s=float(op["nominal_s"]),
                min_s=float(op["min_s"]),
                resources={k: int(v) for k, v in op["resources"].items()},
                depends=tuple(op["depends"]),
                branch=op["branch"],
                evidence=tuple(Step(s["activity"], s["resource"], dict(s.get("attrs", {}))) for s in op["evidence"]),
            )
            for op in sorted(body["operations"], key=lambda o: o["sequence"])
        )
        recipes[name] = Recipe(name, operations)
    return recipes
