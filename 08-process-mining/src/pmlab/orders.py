"""Order correlation: which order each low-level event belongs to.

No event carries an order id. The pallets carry the order through the line,
so the rules start from the loading:

1. Robot missions are paired (started + ended, ruling R1) and grouped into
   the mission sequences of the recipe operations, one robot at a time.
2. A `robot_a` load burst opens an order: one load group per pallet, one
   after the other (less than JOIN_S between them), as long as the loads
   together fit the loads of one recipe. The pallets it places (the load
   bay stays during the place missions) belong to the order.
3. A pallet's later stays belong to the same order until the pallet is
   loaded again (pallet ids are reused).
4. A covers load after a failed covers check (ruling R6) is a reload: it
   joins the order of the failed pallet, not a new order. Exception: it is
   the first load of a new burst when the next load group follows it within
   JOIN_S and completes a recipe load set with it, and that next group does
   not already open a burst with the group after it.
5. Station and cell events join the order of the one stay at their bay that
   holds them. Robot groups at the QC bay join the order of the stay that
   holds the first mission; a `go_to_<bay>_bay` mission joins the stay that
   starts at that bay just after it. A delivery (`take_*_from_pallet` with no
   stay around it) joins the oldest order whose pallet left the mill bay
   with the matching program and that has no delivery yet.

Events that no rule places stay out: no guess. Every link is an inference.

Teaching point: without a case id, correlation is a heuristic. JOIN_S,
ARRIVE_S and the look-ahead of rule 4 are calibrated on the logs of this
unit's simulator (burst gap 0.8-2.5 s, gap between two bookings >= 0.5 s),
not on real data. Their limits are measured, not assumed: test_orders.py
measures precision and coverage on train and shows a case where the burst
rule splits one order in two (a gap between two loads above JOIN_S).
"""

from collections import defaultdict
from dataclasses import dataclass, field

from pmlab.events import Event
from pmlab.recipes import Operation, Recipe, load_recipes
from pmlab.rules import CELL_BAY, order_key, stay_span, stays_at

JOIN_S = 3.0          # most time between two load groups of one burst
ARRIVE_S = 15.0       # most time from the end of a go_to_<bay>_bay mission to the stay start
# The logical line topology (the recipes do not give it): the bay where each
# station or cell works on a pallet, and the bay where each robot handles a
# pallet outside the loading (robot_a handles pallets at the load bay, rule 2;
# its deliveries have no stay, rule 5).
STATION_BAY = {"tester": "tester", "qc_station": "qc", **CELL_BAY}
ROBOT_BAY = {"robot_b": "qc"}


@dataclass
class Mission:
    """One mission: its started and ended events (one may be missing)."""
    resource: str
    mission: str
    start: float
    end: float
    ids: list[str]
    seen_start: bool = True        # False: the start is missing, `start` is the end time


@dataclass
class Group:
    """Consecutive missions of one robot that follow the mission sequence of an operation."""
    resource: str
    units: list[Mission]
    ops: set[str]
    index: int

    @property
    def start(self) -> float:
        return self.units[0].start

    @property
    def end(self) -> float:
        return self.units[-1].end

    @property
    def ids(self) -> list[str]:
        return [i for u in self.units for i in u.ids]


@dataclass
class Order:
    oid: str
    loads: set[str] = field(default_factory=set)
    last_end: float = 0.0
    reloads: int = 0


# --- missions ---------------------------------------------------------------

def mission_units(events: list[Event]) -> list[Mission]:
    """Pair mission_started and mission_ended. A robot runs one mission at a time: an end pairs
    with the last start on that robot if the mission is the same; a start with no end stays alone."""
    open_: dict[str, Mission] = {}
    units = []
    for e in sorted(events, key=order_key):
        if e.activity not in ("mission_started", "mission_ended"):
            continue
        mission = e.attrs.get("mission", "")
        u = open_.pop(e.resource, None)
        if e.activity == "mission_started":
            u = Mission(e.resource, mission, e.time, e.time, [e.event_id])
            open_[e.resource] = u
            units.append(u)
        elif u is not None and u.mission == mission:
            u.end = e.time
            u.ids.append(e.event_id)
        else:   # an end with no start (a gap)
            units.append(Mission(e.resource, mission, e.time, e.time, [e.event_id], seen_start=False))
    return sorted(units, key=lambda u: (u.start, int(u.ids[0][1:])))


def mission_steps(recipes: dict[str, Recipe]) -> dict[str, tuple[str, ...]]:
    """Operation name -> its missions in order (ruling R2: one entry per name)."""
    out = {}
    for recipe in recipes.values():
        for op in recipe.operations:
            names = tuple(s.attrs["mission"] for s in op.evidence if s.activity == "mission")
            if names:
                out[op.name] = names
    return out


def mission_groups(units: list[Mission], steps: dict[str, tuple[str, ...]]) -> list[Group]:
    """Group the missions of each robot by the mission sequences of the operations."""
    groups: list[Group] = []
    current: dict[str, Group] = {}
    for u in units:
        g = current.get(u.resource)
        if g is not None:
            nxt = {op for op in g.ops if g.index + 1 < len(steps[op]) and steps[op][g.index + 1] == u.mission}
            if nxt:
                g.units.append(u)
                g.ops, g.index = nxt, g.index + 1
                continue
        firsts = {op for op, seq in steps.items() if seq[0] == u.mission}
        if firsts:
            g = Group(u.resource, [u], firsts, 0)
        else:   # the first missions are missing, or the mission is unknown
            at = {op: seq.index(u.mission) for op, seq in steps.items() if u.mission in seq}
            index = min(at.values(), default=0)
            g = Group(u.resource, [u], {op for op, i in at.items() if i == index}, index)
        groups.append(g)
        current[u.resource] = g
    return groups


# --- recipe facts -----------------------------------------------------------

def _places(op: Operation) -> bool:
    return any(s.activity == "mission" and s.attrs["mission"].endswith("_on_pallet") for s in op.evidence)


def load_facts(recipes: dict[str, Recipe]) -> tuple[list[frozenset[str]], dict[str, str]]:
    """The load sets (main-branch loads of each recipe) and the reloads: fail op -> the main load
    with the same missions (ruling R6)."""
    sets, by_name = [], {}
    for recipe in recipes.values():
        sets.append(frozenset(op.name for op in recipe.operations if op.branch == "main" and _places(op)))
        for op in recipe.operations:
            by_name[op.name] = op
    reloads = {}
    for op in by_name.values():
        if op.branch == "fail" and _places(op):
            for twin in by_name.values():
                if twin.branch == "main" and twin.evidence == op.evidence:
                    reloads[op.name] = twin.name
    return sets, reloads


def _delivery_programs(recipes: dict[str, Recipe]) -> dict[str, str]:
    """Delivery op (missions only, takes from the pallet) -> the program of the operation it depends on."""
    out = {}
    for recipe in recipes.values():
        ops = {op.name: op for op in recipe.operations}
        for op in recipe.operations:
            missions = [s.attrs["mission"] for s in op.evidence if s.activity == "mission"]
            if len(missions) == len(op.evidence) and missions and missions[0].endswith("_from_pallet"):
                for dep in op.depends:
                    for s in ops[dep].evidence:
                        if s.activity == "program_started":
                            out[op.name] = s.attrs["program"]
    return out


# --- correlation ------------------------------------------------------------

class Pallets:
    """The load segments of each pallet: the order of a pallet at a time is the order of its latest load."""

    def __init__(self) -> None:
        self.loads: dict[int, list[tuple[float, str]]] = defaultdict(list)

    def add(self, pallet: int, start: float, oid: str) -> None:
        self.loads[pallet].append((start, oid))
        self.loads[pallet].sort()

    def order_at(self, pallet: int | None, time: float) -> str | None:
        if pallet is None:
            return None
        found = None
        for start, oid in self.loads.get(pallet, []):
            if start <= time:
                found = oid
        return found


def _overlaps(a: tuple[float, float], b: tuple[float, float]) -> bool:
    return a[0] <= b[1] and b[0] <= a[1]


def correlate(events: list[Event], recipes: dict[str, Recipe] | None = None) -> dict[str, str]:
    """Event id -> "order:<n>" for every event the rules can place; the others are left out."""
    recipes = recipes or load_recipes()
    steps = mission_steps(recipes)
    load_sets, reloads = load_facts(recipes)
    reload_of = {twin: fail for fail, twin in reloads.items()}
    loads = set().union(*load_sets) | set(reloads)
    groups = mission_groups(mission_units(events), steps)
    stays = sorted((e for e in events if e.activity == "bay_stay" and e.pallet is not None), key=order_key)
    out: dict[str, str] = {}

    # 2-4: load bursts, in time order
    load_groups = [g for g in groups if g.resource == "robot_a" and g.ops & loads]
    load_stays = [s for s in stays if s.attrs.get("bay") == "load"]
    fails = []        # (time, qc stay) of each failed check
    for e in events:
        if e.activity == "check_failed":
            held = stays_at(stays, STATION_BAY.get(e.resource, ""), e.time)
            if len(held) == 1:
                fails.append((e.time, held[0]))
    pallets = Pallets()
    orders: list[Order] = []
    opening: Order | None = None

    def fits(kinds: set[str]) -> bool:
        return any(kinds <= s for s in load_sets)

    def failed_before(order: Order, time: float) -> int:
        return sum(1 for t, s in fails if t < time and pallets.order_at(s.pallet, stay_span(s)[0]) == order.oid)

    def kind_of(g: Group) -> str:
        return min(g.ops & set().union(*load_sets), default=None) or reloads.get(min(g.ops), "")

    def chained(a: Group, b: Group, kind: str) -> bool:
        """b follows a closely and the two loads fit one recipe: one burst."""
        other = kind_of(b)
        return b.start - a.end <= JOIN_S and other != kind and fits({kind, other})

    for n, g in enumerate(load_groups):
        kind = kind_of(g)
        places = [u for u in g.units if u.mission.endswith("_on_pallet")] or g.units
        begin = places[0].start
        if not places[0].seen_start and g.units.index(places[0]) > 0:   # the robot was busy until the mission before
            begin = g.units[g.units.index(places[0]) - 1].end
        span = (begin, places[-1].end)
        placed = [s for s in load_stays if _overlaps(stay_span(s), span)]
        after = load_groups[n + 1:n + 3]
        target, reload = None, False
        if opening is not None and g.start - opening.last_end <= JOIN_S and kind not in opening.loads \
                and fits(opening.loads | {kind}):
            target = opening                                     # the burst goes on
        elif kind in reload_of:
            pending = [o for o in orders if failed_before(o, g.start) > o.reloads]
            starts_burst = len(after) >= 1 and chained(g, after[0], kind) and not (
                len(after) == 2 and chained(after[0], after[1], kind_of(after[0])))
            if pending and not starts_burst:
                target, reload = pending[0], True                # the reload joins the failed order
                target.reloads += 1
        if target is None:
            target = Order(f"order:{len(orders) + 1}")
            orders.append(target)
        if not reload:                                           # a load of the burst
            target.loads.add(kind)
            target.last_end = g.end
            opening = target
        for s in placed:
            pallets.add(s.pallet, stay_span(s)[0], target.oid)
        for i in g.ids + [s.event_id for s in placed]:
            out[i] = target.oid

    # 3: the later stays of each pallet
    for s in stays:
        oid = pallets.order_at(s.pallet, stay_span(s)[0])
        if oid is not None and s.event_id not in out:
            out[s.event_id] = oid
    placed_stays = [s for s in stays if s.event_id in out]

    def holding(bay: str, time: float) -> str | None:
        held = stays_at(placed_stays, bay, time)
        return out[held[0].event_id] if len(held) == 1 else None

    # 5: station and cell events
    for e in events:
        if e.resource in STATION_BAY and e.event_id not in out:
            oid = holding(STATION_BAY[e.resource], e.time)
            if oid is not None:
                out[e.event_id] = oid

    # 5: robot groups at a bay
    deliveries = []
    for g in groups:
        if g in load_groups:
            continue
        first = g.units[0]
        oid = None
        if first.mission.startswith("go_to_") and first.mission.endswith("_bay"):
            bay = first.mission[len("go_to_"):-len("_bay")]
            nxt = [s for s in placed_stays if s.attrs.get("bay") == bay
                   and first.start <= stay_span(s)[0] <= first.end + ARRIVE_S]
            oid = out[nxt[0].event_id] if nxt else None
        elif g.resource in ROBOT_BAY:
            oid = holding(ROBOT_BAY[g.resource], first.start)
        elif first.mission.endswith("_from_pallet"):
            deliveries.append(g)
        if oid is not None:
            for i in g.ids:
                out[i] = oid

    # 5: deliveries, oldest waiting order first
    programs = _delivery_programs(recipes)
    by_id = {e.event_id: e for e in events}
    mill_ends = []    # (end, order, program) of each placed mill stay
    for s in placed_stays:
        if s.attrs.get("bay") == CELL_BAY["mill_cell"] and not s.attrs.get("open"):
            progs = {by_id[i].attrs.get("program") for i, oid in out.items()
                     if oid == out[s.event_id] and by_id[i].resource == "mill_cell"
                     and stay_span(s)[0] <= by_id[i].time <= s.time}
            mill_ends.append((s.time, out[s.event_id], progs))
    mill_ends.sort(key=lambda m: m[0])
    delivered: set[str] = set()
    for g in sorted(deliveries, key=lambda g: g.start):
        wanted = {programs[op] for op in g.ops if op in programs}
        waiting = [oid for end, oid, progs in mill_ends
                   if end <= g.start and oid not in delivered and progs & wanted]
        if waiting:
            delivered.add(waiting[0])
            for i in g.ids:
                out[i] = waiting[0]

    # derived events follow the events they cite
    for e in events:
        if e.event_id not in out and e.evidence:
            cited = {out.get(i) for i in e.evidence if by_id.get(i) and by_id[i].activity != "bay_stay"}
            cited.discard(None)
            if len(cited) == 1:
                out[e.event_id] = cited.pop()
    return out
