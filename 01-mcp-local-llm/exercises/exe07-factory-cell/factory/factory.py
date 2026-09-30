import random
from datetime import date, datetime, timedelta
from pathlib import Path

from pydantic import BaseModel, ValidationError

from .config import Production, Recipe, load_recipe
from .logbook import LogBook
from .part import Part
from .station import Station, load_station_types

FAULT_PREFIX = "fault:"
# Productions are separate days. Only the time of day appears in the logs;
# internally each production gets its own calendar day, starting here.
FIRST_DAY = date(2026, 1, 1)


class Cause(BaseModel):
    station: str
    fault: str
    parts: list[str]


class Truth(BaseModel):
    """What really happened, computed from the parts themselves."""

    stored: list[str]
    rejected: list[str]
    scrapped: list[str]
    unfinished: list[str]
    rejected_by_production: dict[str, list[str]]
    first_rejected: str | None
    causes: list[Cause]


class Factory:
    """The root object: builds the stations of a recipe and runs the clock."""
    
    recipe: Recipe
    logbook: LogBook
    parts: list[Part]
    stations: dict[str, Station]

    def __init__(self, recipe: Recipe) -> None:
        self.recipe = recipe
        self.logbook = LogBook()
        self.parts: list[Part] = []
        self.stations: dict[str, Station] = {}

        types = load_station_types()
        for spec in recipe.stations:
            cls = types.get(spec.type)
            if cls is None:
                raise ValueError(
                    f"station {spec.id}: unknown type {spec.type!r}. Known types: {sorted(types)}"
                )
            try:
                params = cls.Params.model_validate(spec.params)
            except ValidationError as exc:
                raise ValueError(f"station {spec.id} ({spec.type}): invalid params\n{exc}") from exc
            rng = random.Random(f"{recipe.seed}-{spec.id}")
            self.stations[spec.id] = cls(spec.id, params, self.logbook, rng)

        days = {p.id: FIRST_DAY + timedelta(days=i) for i, p in enumerate(recipe.productions)}
        self._faults: list[tuple[datetime, Station, str, BaseModel]] = []
        for fault in recipe.faults:
            target = self.stations[fault.station]
            model = target.faults.get(fault.kind)
            if model is None:
                raise ValueError(
                    f"station {target.id} ({target.type_name}) does not support fault "
                    f"{fault.kind!r}. Supported: {sorted(target.faults)}"
                )
            try:
                params = model.model_validate(fault.params)
            except ValidationError as exc:
                raise ValueError(f"fault {fault.kind} at {fault.at} on {target.id}: invalid\n{exc}") from exc
            when = datetime.combine(days[fault.production], fault.at)
            self._faults.append((when, target, fault.kind, params))

    @classmethod
    def from_yaml(cls, path: str | Path) -> "Factory":
        return cls(load_recipe(path))

    def run(self) -> "Factory":
        """Simulate every production, one second at a time.

        Stations keep their state between productions (for example tool wear),
        and unfinished parts wait in the cell for the next production.
        """
        for day, production in enumerate(self.recipe.productions):
            self._run_production(production, FIRST_DAY + timedelta(days=day))
        return self

    def _run_production(self, production: Production, day: date) -> None:
        recipe = self.recipe
        orders = production.orders
        backlog: list[Part] = []
        released = 0
        first = self.stations[recipe.route[0]]
        start = datetime.combine(day, production.start)
        end = datetime.combine(day, production.end)
        self.logbook.production = production.id

        for current in self.stations.values():
            current.log(start, "PRODUCTION_START", production=production.id)

        for second in range(int((end - start).total_seconds())):
            t = start + timedelta(seconds=second)

            if released < orders.count and second % orders.release_every_s == 0:
                part = Part(
                    id=f"P-{recipe.first_part_id + len(self.parts):04d}",
                    production=production.id,
                    route=list(recipe.route),
                    nominal_mm=recipe.part.nominal_mm,
                    tolerance_mm=recipe.part.tolerance_mm,
                )
                self.parts.append(part)
                backlog.append(part)
                released += 1

            while backlog and first.can_accept():
                first.receive(backlog.pop(0), t)

            for when, target, kind, params in self._faults:
                if when == t:
                    target.apply_fault(kind, params, t)

            for current in self.stations.values():
                current.step(t)

            self._move_parts(t)

        # Logged at the last simulated second, so it falls inside [start, end).
        for current in self.stations.values():
            current.log(end - timedelta(seconds=1), "PRODUCTION_END", production=production.id)

    def _move_parts(self, t: datetime) -> None:
        for current in self.stations.values():
            while current.outbox:
                part = current.outbox[0]
                if part.status != "in_progress" or part.is_last_stop:
                    current.outbox.popleft()
                    continue
                target = self.stations[part.route[part.stop + 1]]
                if not target.can_accept():
                    break
                current.outbox.popleft()
                part.stop += 1
                target.receive(part, t)

    def truth(self) -> Truth:
        by_status = {status: [p.id for p in self.parts if p.status == status]
                     for status in ("stored", "rejected", "scrapped", "in_progress")}

        causes: dict[tuple[str, str], list[str]] = {}
        for part in self.parts:
            if part.status != "rejected":
                continue
            for c in part.contributions:
                if c.cause.startswith(FAULT_PREFIX):
                    causes.setdefault((c.station, c.cause.removeprefix(FAULT_PREFIX)), []).append(part.id)

        rejected_by_production: dict[str, list[str]] = {}
        for part in self.parts:
            if part.status == "rejected":
                rejected_by_production.setdefault(part.production, []).append(part.id)

        return Truth(
            rejected_by_production=rejected_by_production,
            stored=by_status["stored"],
            rejected=by_status["rejected"],
            scrapped=by_status["scrapped"],
            unfinished=by_status["in_progress"],
            first_rejected=by_status["rejected"][0] if by_status["rejected"] else None,
            causes=[Cause(station=s, fault=f, parts=p) for (s, f), p in causes.items()],
        )
