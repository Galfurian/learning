"""Event abstraction: low-level events of one order become operations with a start and a complete.

The order's recipe is not known, so the events are matched against the
operations of all recipes, by operation name (ruling R2). A step matches an
event when the activity, the resource and every attr of the step are equal;
when several operations match, the most specific step wins (more attrs).
Missions count as one unit: started + ended (ruling R1).

Inside one order, in time order:
1. Every event except the bay stays joins the latest instance of its
   operation, or starts a new one when that instance already has the step.
   Context rules:
   - a fail-branch operation (reload_covers) wins over its twin
     (load_covers) once all the operations it depends on (bin_covers) have
     started in the order (ruling R6);
   - when the step is shared (deliver_to_storage), the operation whose latest
     instance still lacks the step wins;
   - consecutive started/done pairs on the same cell for the same operation
     are one operation (the assembly is done in parts);
   - an exact copy of an event of the instance joins it (a duplicate record).
2. The bay stays: the first load stay of the order reserves the pallet; a
   stay joins an instance of its operation that has evidence inside the stay
   and no stay yet; a stay with cell events of its bay inside it, or a load
   stay during a place mission, is extra evidence of that operation; any other
   stay starts its own operation.
3. An event that matches no operation is kept as `unmapped:<activity>`.

The start entry has the time of the first evidence (a stay starts at
attrs.start), the complete entry the time of the last. An operation has no
complete when a stay is still open (attrs.open), when a stay step has no
closed stay, or when its last evidence is a start with no end.
"""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from pmlab.events import Event
from pmlab.log import Entry
from pmlab.orders import mission_units
from pmlab.recipes import Operation, Recipe, Step
from pmlab.rules import CELL_BAY, number, order_key, stay_span

CLAIM = "inferred"
STARTS = {"operation_started", "program_started"}


@dataclass
class Unit:
    """One piece of evidence: a mission (one or two events) or one event."""
    activity: str                  # "mission" for a mission
    resource: str
    attrs: dict[str, Any]
    begin: float
    end: float
    ids: list[str]
    pallet: int | None = None
    open: bool = False             # a stay still open, or a mission with no end
    start_only: bool = False       # the start of something with no end in the unit

    @property
    def first(self) -> int:
        return number(self.ids[0])


@dataclass
class Instance:
    op: Operation
    units: dict[int, Unit] = field(default_factory=dict)     # step index -> unit
    extra: list[Unit] = field(default_factory=list)

    @property
    def begin(self) -> float:
        return min(u.begin for u in self.units.values())


def matches(step: Step, unit: Unit) -> bool:
    """The unit is evidence of the step: same activity and resource, and every attr of the step."""
    return (step.activity == unit.activity and step.resource == unit.resource
            and all(unit.attrs.get(k) == v for k, v in step.attrs.items()))


def evidence_units(events: list[Event]) -> list[Unit]:
    """The evidence units of one order. A derived program event carries the change it cites."""
    units = []
    by_id = {e.event_id: e for e in events}
    for m in mission_units(events):
        attrs = dict(by_id[m.ids[0]].attrs)
        only_start = len(m.ids) == 1 and by_id[m.ids[0]].activity == "mission_started"
        units.append(Unit("mission", m.resource, attrs, m.start, m.end, list(m.ids),
                          open=only_start, start_only=only_start))
    derived = {e.event_id: [i for i in e.evidence if i in by_id and by_id[i].activity == "signal_changed"]
               for e in events if e.claim_kind in ("derived", "inferred") and e.activity in
               ("program_started", "program_ended")}
    cited = {i for ids in derived.values() for i in ids}
    for e in events:
        if e.activity in ("mission_started", "mission_ended") or e.event_id in cited:
            continue
        ids = [e.event_id] + derived.get(e.event_id, [])
        if e.activity == "bay_stay":
            start, end = stay_span(e)
            units.append(Unit("bay_stay", e.resource, dict(e.attrs), start, end, ids, e.pallet,
                              open=bool(e.attrs.get("open"))))
        else:
            units.append(Unit(e.activity, e.resource, dict(e.attrs), e.time, e.time, ids, e.pallet))
    units.sort(key=lambda u: (u.begin, u.first))
    return units


def same_record(a: Unit, b: Unit) -> bool:
    """Two records of one thing (a duplicated event): equal but for the event ids."""
    return (a.activity, a.resource, a.attrs, a.begin, a.end) == (b.activity, b.resource, b.attrs, b.begin, b.end)


class Case:
    def __init__(self, ops: dict[str, Operation], recipes: dict[str, Recipe]) -> None:
        self.ops = ops
        self.recipes = recipes
        self.instances: list[Instance] = []
        self.unmapped: list[Unit] = []

    def latest(self, name: str) -> Instance | None:
        found = [i for i in self.instances if i.op.name == name]
        return found[-1] if found else None

    def candidates(self, unit: Unit) -> list[tuple[str, int]]:
        """(operation, step index) pairs of the most specific matching steps."""
        found = [(name, n, len(step.attrs)) for name, op in self.ops.items()
                 for n, step in enumerate(op.evidence) if matches(step, unit)]
        if not found:
            return []
        best = max(k for *_, k in found)
        return [(name, n) for name, n, k in found if k == best]

    def started(self, name: str, before: float) -> bool:
        return any(i.op.name == name and i.begin <= before for i in self.instances)

    def fail_filter(self, names: set[str], unit: Unit) -> set[str]:
        """Ruling R6: a fail-branch twin wins once its dependencies have started; before, it cannot run."""
        fail = {n for n in names if self.ops[n].branch == "fail"}
        ready = {n for n in fail if all(self.started(d, unit.begin) for d in self.ops[n].depends)}
        if ready:
            return ready
        return (names - fail) or names

    def in_context(self, names: set[str]) -> str:
        """Among new operations, one of a recipe that holds the operations seen so far."""
        seen = {i.op.name for i in self.instances}
        fits = [n for n in sorted(names) if any(
            {n} | seen <= {op.name for op in r.operations} for r in self.recipes.values())]
        return (fits or sorted(names))[0]

    def new(self, name: str) -> Instance:
        inst = Instance(self.ops[name])
        self.instances.append(inst)
        return inst

    def place(self, unit: Unit) -> None:
        """Rule 1: an event that is not a bay stay."""
        cands = self.candidates(unit)
        if not cands:
            self.unmapped.append(unit)
            return
        names = self.fail_filter({n for n, _ in cands}, unit)
        steps = {n: [i for c, i in cands if c == n] for n in names}
        # The operation with the most recent instance first (a larger index is more recent, so it is
        # negated). Operations with no instance yet (key 0) are skipped in the loop; if no instance
        # takes the unit, it starts a new instance below.
        for name in sorted(names, key=lambda n: -self.instances.index(self.latest(n)) if self.latest(n) else 0):
            inst = self.latest(name)
            if inst is None:
                continue
            if any(same_record(unit, u) for u in list(inst.units.values()) + inst.extra):
                inst.extra.append(unit)                        # a duplicate record
                return
            free = [i for i in steps[name] if i not in inst.units]
            if free:
                inst.units[free[0]] = unit
                return
            if self.consecutive(inst, unit):
                inst.extra.append(unit)
                return
        name = self.in_context(names)
        self.new(name).units[steps[name][0]] = unit

    def consecutive(self, inst: Instance, unit: Unit) -> bool:
        """One more started/done pair of the same cell operation, with no other operation on the cell between."""
        if unit.activity not in ("operation_started", "operation_done") or unit.resource not in CELL_BAY:
            return False
        if not all(s.resource == unit.resource for s in inst.op.evidence):
            return False
        later = [i for i in self.instances if i is not inst and i.begin >= inst.begin
                 and any(u.resource == unit.resource for u in i.units.values())]
        return not later

    def place_stay(self, unit: Unit) -> None:
        """Rule 2: a bay stay."""
        bay = unit.attrs.get("bay")
        cands = self.candidates(unit)
        names = {n for n, _ in cands}
        reserve = sorted(n for n in names if all(s.activity == "bay_stay" for s in self.ops[n].evidence))
        if bay == "load" and reserve and not any(i.op.name in reserve for i in self.instances):
            self.new(self.in_context(set(reserve))).units[0] = unit
            return
        for inst in self.instances:     # a duplicate record of a stay
            if any(same_record(unit, u) for u in list(inst.units.values()) + inst.extra):
                inst.extra.append(unit)
                return
        inside = [inst for inst in self.instances if inst.op.name in names
                  and not any(u.activity == "bay_stay" for u in inst.units.values())
                  and any(unit.begin <= u.begin <= unit.end for u in inst.units.values())]
        if inside:
            inst = inside[0]
            step = next(i for c, i in cands if c == inst.op.name)
            inst.units[step] = unit
            return
        for inst in self.instances:
            if self.at_bay(inst, unit, bay):
                inst.extra.append(unit)
                return
        if names:
            name = self.in_context(names)
            self.new(name).units[next(i for c, i in cands if c == name)] = unit
        else:
            self.unmapped.append(unit)

    @staticmethod
    def at_bay(inst: Instance, stay: Unit, bay: str) -> bool:
        """The instance works on a pallet at this bay during the stay."""
        for u in inst.units.values():
            if CELL_BAY.get(u.resource) == bay and stay.begin <= u.begin <= stay.end:
                return True
            if bay == "load" and u.activity == "mission" and u.attrs.get("mission", "").endswith("_on_pallet") \
                    and u.begin <= stay.end and stay.begin <= u.end:
                return True
        return False


def _timed(inst: Instance) -> list[Unit]:
    """The units that give the times: the matched steps, plus extra units that match a step of the
    operation (more assembly parts, duplicates). Stays that are only extra evidence do not count."""
    return list(inst.units.values()) + [u for u in inst.extra if any(matches(s, u) for s in inst.op.evidence)]


def _complete(inst: Instance) -> bool:
    units = _timed(inst)
    if any(u.open and u.activity == "bay_stay" for u in units):
        return False
    if any(s.activity == "bay_stay" for s in inst.op.evidence) and not any(u.activity == "bay_stay" for u in units):
        return False
    last = max(units, key=lambda u: (u.end, u.first))
    return not last.start_only and last.activity not in STARTS     # the last evidence is not a bare start


def _objects(case_id: str, units: list[Unit], more: frozenset[int] = frozenset()) -> tuple[str, ...]:
    pallets = sorted({u.pallet for u in units if u.pallet is not None} | more)
    resources = sorted({u.resource for u in units if u.resource != "conveyor"})
    return (case_id, *(f"pallet:{p}" for p in pallets), *resources)


def _sources(units: list[Unit]) -> tuple[str, ...]:
    return tuple(sorted({i for u in units for i in u.ids}, key=number))


def _pallets(inst: Instance) -> set[int]:
    return {u.pallet for u in list(inst.units.values()) + inst.extra if u.pallet is not None}


def _more_pallets(case: Case, inst: Instance) -> frozenset[int]:
    """Ruling R8: pallets that an operation uses with no stay of its own.
    - reserve_pallet holds every pallet loaded in the first load burst: the load stays that
      begin while the first load operations (load_board, load_covers, load_bricks) run;
    - assemble_gadget also holds the pallet of the board, buffered by buffer_board."""
    if inst.op.name == "reserve_pallet":
        loads = [i for n in ("load_board", "load_covers", "load_bricks")
                 if (i := next((i for i in case.instances if i.op.name == n), None))]
        if not loads:
            return frozenset()
        low = min(u.begin for i in loads for u in _timed(i))
        high = max(u.end for i in loads for u in _timed(i))
        stays = [u for i in case.instances for u in list(i.units.values()) + i.extra
                 if u.activity == "bay_stay" and u.attrs.get("bay") == "load" and u.pallet is not None
                 and low <= u.begin <= high]
        return frozenset(u.pallet for u in stays)
    if inst.op.name == "assemble_gadget":
        return frozenset(p for i in case.instances if i.op.name == "buffer_board" and i.begin <= inst.begin
                         for p in _pallets(i))
    return frozenset()


def _entries(case_id: str, case: Case) -> list[Entry]:
    out = []
    for inst in case.instances:
        units = _timed(inst)
        every = list(inst.units.values()) + inst.extra
        resource = next((u.resource for u in sorted(units, key=lambda u: (u.begin, u.first))
                         if u.resource != "conveyor"), "conveyor")
        base = {"case_id": case_id, "activity": inst.op.name, "resource": resource,
                "objects": _objects(case_id, every, _more_pallets(case, inst)), "source_ids": _sources(every), "claim_kind": CLAIM}
        out.append(Entry(lifecycle="start", time=min(u.begin for u in units), **base))
        if _complete(inst):
            out.append(Entry(lifecycle="complete", time=max(u.end for u in units), **base))
    for u in case.unmapped:
        out.append(Entry(case_id, "unmapped:" + u.activity, "complete", u.end, u.resource,
                         _objects(case_id, [u]), _sources([u]), CLAIM))
    return out


def operations_by_name(recipes: dict[str, Recipe]) -> dict[str, Operation]:
    """Ruling R2: one operation per name over all recipes."""
    out = {}
    for recipe in recipes.values():
        for op in recipe.operations:
            out.setdefault(op.name, op)
    return out


def match_operations(case: Case, units: list[Unit]) -> None:
    """Rule 1 for one order: each unit that is not a bay stay, in time order, joins an
    operation instance of the case (or case.unmapped). EXE02 asks for this function."""
    for u in units:
        if u.activity != "bay_stay":
            case.place(u)


def abstract(events: list[Event], recipes: dict[str, Recipe], orders: dict[str, str],
             match: Callable[[Case, list[Unit]], None] = match_operations) -> list[Entry]:
    """Entries of every order in `orders` (event id -> order id), sorted by time.
    Events with no order are left out. `match` places the units that are not bay
    stays (rule 1); the bay stays follow (rule 2)."""
    ops = operations_by_name(recipes)
    by_case: dict[str, list[Event]] = {}
    for e in sorted(events, key=order_key):
        if e.event_id in orders:
            by_case.setdefault(orders[e.event_id], []).append(e)
    entries = []
    for case_id, case_events in by_case.items():
        units = evidence_units(case_events)
        case = Case(ops, recipes)
        match(case, units)
        for u in units:
            if u.activity == "bay_stay":
                case.place_stay(u)
        entries += _entries(case_id, case)
    return sorted(entries, key=lambda e: (e.time, e.lifecycle != "start", number(e.source_ids[0]), e.case_id))
