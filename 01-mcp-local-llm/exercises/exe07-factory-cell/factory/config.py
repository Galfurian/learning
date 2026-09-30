from datetime import time
from pathlib import Path
from typing import Annotated, Any

import yaml
from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, PlainSerializer, model_validator


def parse_hhmm(value: Any) -> time:
    """Military time: '0952' is 09:52."""
    if isinstance(value, time):
        return value
    if not isinstance(value, str):
        # Unquoted in YAML, 0700 is the octal number 448: refuse to guess.
        raise ValueError(f"write military times as quoted strings, e.g. '0700', got {value!r}")
    text = value
    if len(text) != 4 or not text.isdigit():
        raise ValueError(f"expected military time HHMM, got {value!r}")
    return time(int(text[:2]), int(text[2:]))


def hhmm(value: time) -> str:
    return f"{value:%H%M}"


# A time of day written as HHMM, e.g. "0952".
HHMM = Annotated[time, BeforeValidator(parse_hhmm), PlainSerializer(hhmm)]


class PartSpec(BaseModel):
    """What a finished part must measure."""

    nominal_mm: float
    tolerance_mm: float = Field(gt=0)


class Orders(BaseModel):
    """How raw parts enter the cell during one production."""

    count: int = Field(gt=0)
    release_every_s: int = Field(gt=0)


class Production(BaseModel):
    """One production order: one day of work, from ``start`` to ``end``."""

    id: str
    start: HHMM
    end: HHMM
    orders: Orders

    @model_validator(mode="after")
    def _check_window(self) -> "Production":
        if self.end <= self.start:
            raise ValueError(f"production {self.id}: end must be after start")
        return self


class StationSpec(BaseModel):
    """One station instance. ``params`` are validated by the station type."""

    id: str
    type: str
    params: dict[str, Any] = {}


class FaultSpec(BaseModel):
    """A fault injected at a given time of day.

    Fields other than ``at``, ``station`` and ``kind`` are the fault's own
    parameters; the station type validates them.
    """

    model_config = ConfigDict(extra="allow")

    production: str
    at: HHMM
    station: str
    kind: str

    @property
    def params(self) -> dict[str, Any]:
        return dict(self.model_extra or {})


class Recipe(BaseModel):
    """A production line and its life: stations, route, productions, faults."""

    name: str
    seed: int = 0
    first_part_id: int = 1
    part: PartSpec
    stations: list[StationSpec]
    route: list[str] = Field(min_length=1)
    productions: list[Production] = Field(min_length=1)
    faults: list[FaultSpec] = []

    @model_validator(mode="after")
    def _check_references(self) -> "Recipe":
        ids = [spec.id for spec in self.stations]
        duplicates = {i for i in ids if ids.count(i) > 1}
        if duplicates:
            raise ValueError(f"duplicate station ids: {sorted(duplicates)}")
        for name in self.route:
            if name not in ids:
                raise ValueError(f"route uses unknown station {name!r}")
        productions = {p.id: p for p in self.productions}
        if len(productions) != len(self.productions):
            raise ValueError("duplicate production ids")
        for fault in self.faults:
            if fault.station not in ids:
                raise ValueError(f"fault uses unknown station {fault.station!r}")
            production = productions.get(fault.production)
            if production is None:
                raise ValueError(f"fault uses unknown production {fault.production!r}")
            if not production.start <= fault.at < production.end:
                raise ValueError(
                    f"fault at {hhmm(fault.at)} is outside {production.id} "
                    f"({hhmm(production.start)}-{hhmm(production.end)})"
                )
        return self

    def to_yaml(self) -> str:
        return yaml.safe_dump(self.model_dump(mode="json"), sort_keys=False)


def load_recipe(path: str | Path) -> Recipe:
    return Recipe.model_validate(yaml.safe_load(Path(path).read_text()))
