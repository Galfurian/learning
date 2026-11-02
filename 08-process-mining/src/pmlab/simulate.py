"""Play the recipes out into low-level events in the unit 07 export shape.

The generator is seeded and deterministic. Orders arrive over time and run at
the same time; they share the robots, the stations, the bays and a pool of
ten pallets whose ids are reused. Each resource serves one use at a time,
first come first served, so orders wait.

What the events show:
- each operation emits the evidence steps of its recipe (src/pmlab/data/recipes.yaml):
  a "mission" step is a mission_started and mission_ended pair (ruling R1),
  program_started/ended are signal_changed events on mill_cell (the extra
  rules of Task 3 derive them), check and test results, cell operations;
- every time a pallet stands at a bay there is one bay_stay event at the end
  of the stay (attrs.start, attrs.corroborated), also where the recipe does
  not list it as evidence (the second load stay of an order, the covers
  pallet at the assembly bay): that is what the line records;
- robot, station and cell events have no pallet; no event has an order id.
  The true order of each event is in the truth dict only.

The physical route (which pallet carries an operation, at which bay) is not
in the recipe; CARRIER below gives it.
"""

import math
import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from pmlab.events import Event
from pmlab.recipes import Operation, Recipe, Step

SIGMA = 0.25                 # log-normal spread of the durations
MEAN_GAP_S = 300.0           # mean time between two order arrivals
PALLETS = tuple(range(1, 11))
GAP_S = 0.5                  # minimum free time between two uses of one resource
TRANSIT_S = (8.0, 25.0)      # a pallet moves from one bay to the next
MAX_FAILS = 2                # a covers check fails at most twice in one order
KINDS = ("skip", "extra", "swap", "gap", "stuck", "duplicate")
ROUND = 3

# The pallet role that carries each operation (the recipe does not say it).
CARRIER = {
    "load_board": "board", "test_board": "board", "buffer_board": "board",
    "load_covers": "covers", "check_covers": "covers", "bin_covers": "covers", "reload_covers": "covers",
    "assemble_gadget": "covers", "engrave_gadget": "covers", "deliver_gadget": "covers",
    "mill_part": "covers", "deliver_part": "covers",
    "load_bricks": "bricks", "build_bricks": "bricks", "check_bricks": "bricks", "unbuild_bricks": "bricks",
}
CELL_BAY = {"assembly_cell": "assembly", "mill_cell": "mill"}
CLAIM = {
    "mission_started": "observed", "mission_ended": "observed", "bay_stay": "derived",
    "check_passed": "derived", "check_failed": "derived", "test_result": "observed",
    "operation_started": "observed", "operation_done": "observed", "signal_changed": "observed",
}
PROGRAM_STATE = {"program_started": (False, True), "program_ended": (True, False)}


@dataclass
class Raw:
    """An event before it has an id. `slot` names the pallet role until a pallet is chosen.
    `task` labels one occurrence of an operation; `extra` marks the events of an extra operation."""
    activity: str
    resource: str
    time: float
    attrs: dict[str, Any]
    op: str
    task: str = ""
    slot: str | None = None
    pallet: int | None = None
    seq: int = 0
    extra: bool = False


# --- event builders -------------------------------------------------------

def _mission(step: Step, s: float, e: float, op: str) -> list[Raw]:
    return [Raw("mission_started", step.resource, s, dict(step.attrs), op),
            Raw("mission_ended", step.resource, e, dict(step.attrs), op)]


def _stay(bay: str, slot: str | None, s: float, e: float, op: str, **extra: Any) -> Raw:
    return Raw("bay_stay", "conveyor", e, {"bay": bay, "start": s, "corroborated": True, **extra}, op, slot=slot)


def _point(step: Step, t: float, op: str, **extra: Any) -> Raw:
    """A one-time step. program_started/ended become a signal_changed on the cell."""
    if step.activity in PROGRAM_STATE:
        old, new = PROGRAM_STATE[step.activity]
        attrs = {"signal": "program_running", "old": old, "new": new, **step.attrs}
        return Raw("signal_changed", step.resource, t, attrs, op)
    return Raw(step.activity, step.resource, t, {**step.attrs, **extra}, op)


def _missions(steps: list[Step], s: float, e: float, op: str, rng: random.Random) -> tuple[list[Raw], list[tuple]]:
    """Missions one after the other over [s, e]. Returns the events and the robot uses."""
    if not steps:
        return [], []
    gap = min(1.5, 0.05 * (e - s))
    weights = [rng.uniform(0.7, 1.3) for _ in steps]
    work = (e - s) - gap * (len(steps) - 1)
    raws, uses, t = [], [], s
    for step, w in zip(steps, weights):
        d = work * w / sum(weights)
        raws += _mission(step, t, t + d, op)
        uses.append((step.resource, t, t + d))
        t += d + gap
    return raws, uses


# --- resources ------------------------------------------------------------

class Calendar:
    """Busy intervals per resource. A use may not overlap another, with GAP_S between them."""

    def __init__(self) -> None:
        self.busy: dict[str, list[tuple[float, float]]] = defaultdict(list)

    def conflict(self, res: str, s: float, e: float) -> float | None:
        ends = [b for a, b in self.busy[res] if s < b + GAP_S and a < e + GAP_S]
        return max(ends) if ends else None

    def place(self, t: float, uses: list[tuple[str, float, float]]) -> float:
        """The earliest start >= t at which every use (resource, offset start, offset end) is free."""
        while True:
            shift = None
            for res, s, e in uses:
                end = self.conflict(res, t + s, t + e)
                if end is not None:
                    cand = end + GAP_S - s
                    shift = cand if shift is None else max(shift, cand)
            if shift is None:
                return t
            t = max(shift, t + 1e-3)

    def book(self, t: float, uses: list[tuple[str, float, float]]) -> None:
        for res, s, e in uses:
            self.busy[res].append((t + s, t + e))


# --- one order ------------------------------------------------------------

STATIONS = {"tester", "qc_station", "assembly_cell", "mill_cell"}


def _bay(op: Operation) -> str | None:
    """The bay the pallet stands at during the operation: from the bay_stay step, else from the cell."""
    for step in op.evidence:
        if step.activity == "bay_stay":
            return step.attrs["bay"]
    for step in op.evidence:
        if step.resource in CELL_BAY:
            return CELL_BAY[step.resource]
    return None


def _is_reserve(op: Operation) -> bool:
    return not op.depends and all(s.activity == "bay_stay" for s in op.evidence)


def _is_load(op: Operation) -> bool:
    return op.branch == "main" and any(
        s.activity == "mission" and s.attrs["mission"].endswith("_on_pallet") for s in op.evidence)


def _fail_ops(recipe: Recipe) -> list[Operation]:
    """The fail branch in sequence: the removal, then the reload (empty if the recipe has none)."""
    return sorted((op for op in recipe.operations if op.branch == "fail"), key=lambda o: o.sequence)


@dataclass
class Task:
    key: str
    op: Operation
    deps: list[str]
    extra: bool = False          # a deviation "extra": its events belong to no order
    force_pass: bool = False


@dataclass
class OrderRun:
    recipe: Recipe
    rng: random.Random
    cal: Calendar
    pallet_free: dict[int, float]                               # pallet -> free from this time
    fail_p: float
    raws: list[Raw] = field(default_factory=list)
    done: dict[str, float] = field(default_factory=dict)        # task key -> end
    slot_of: dict[str, str] = field(default_factory=dict)       # role -> current slot
    slot_ready: dict[str, float] = field(default_factory=dict)  # slot -> the pallet can be at a bay
    slot_end: dict[str, float] = field(default_factory=dict)    # slot -> its last use
    pallet_of: dict[str, int] = field(default_factory=dict)     # slot -> pallet id
    fails: int = 0
    count: int = 0

    def draw(self, op: Operation) -> float:
        return max(op.min_s, self.rng.lognormvariate(math.log(op.nominal_s), SIGMA))

    def label(self, name: str) -> str:
        self.count += 1
        return f"{name}#{self.count}"

    def emit(self, raws: list[Raw], t: float) -> None:
        for r in raws:
            r.time += t
            if r.activity == "bay_stay":
                r.attrs["start"] += t
            if r.slot is not None:
                r.pallet = self.pallet_of[r.slot]
            self.raws.append(r)

    def use_slot(self, slot: str, end: float) -> None:
        self.slot_ready[slot] = end + self.rng.uniform(*TRANSIT_S)
        self.slot_end[slot] = max(self.slot_end.get(slot, 0.0), end)

    def load(self, ops: list[Operation], ready: float, reserve: str | None) -> None:
        """One robot_a burst that loads one pallet per operation. Each pallet stands at the
        load bay while the robot places on it; the first stay is the reserve evidence."""
        raws, uses, slots, cursor = [], [], [], 0.0
        for op in ops:
            steps = [s for s in op.evidence if s.activity == "mission"]
            d = self.draw(op)
            m_raws, m_uses = _missions(steps, cursor, cursor + d, op.name, self.rng)
            task = self.label(op.name)
            for r in m_raws:
                r.task = task
            places = [u for u, st in zip(m_uses, steps) if st.attrs["mission"].endswith("_on_pallet")]
            p_s, p_e = places[0][1], places[-1][2]
            s = p_s + self.rng.uniform(2.0, min(6.0, 0.2 * (p_e - p_s)))
            e = p_e - self.rng.uniform(3.0, min(9.0, 0.25 * (p_e - p_s)))
            role = CARRIER[op.name]
            slot = f"{role}{len(self.pallet_of) + len(slots)}"   # unique in the order
            stay = _stay("load", slot, s, e, op.name)
            stay.task = task
            if reserve and not slots:
                stay.op, stay.task = reserve, self.label(reserve)
            raws += m_raws + [stay]
            uses += m_uses + [("bay:load", s, e)]
            slots.append((slot, s, e, op.name, stay.task, task, m_uses[-1][2]))
            cursor += d + self.rng.uniform(0.8, 2.5)
        t = ready
        while True:   # the burst waits for the robot, the bay and a free pallet
            t = self.cal.place(t, uses)
            chosen: list[int] = []
            for slot, s, *_ in slots:
                free = [p for p in PALLETS if self.pallet_free[p] <= t + s and p not in chosen]
                if not free:
                    t = min(self.pallet_free[p] for p in PALLETS
                            if p not in chosen and self.pallet_free[p] < math.inf) - s + GAP_S
                    break
                chosen.append(self.rng.choice(free))
            else:
                break
        self.cal.book(t, uses)
        for (slot, s, e, op_name, stay_task, task, m_end), pallet in zip(slots, chosen):
            self.pallet_free[pallet] = math.inf
            self.pallet_of[slot] = pallet
            self.slot_of[CARRIER[op_name]] = slot
            self.use_slot(slot, t + e)
            self.done[op_name] = t + m_end
            if reserve and stay_task.startswith(reserve):
                self.done[reserve] = t + e
        self.emit(raws, t)

    def station(self, task: Task, ready: float, bay: str) -> None:
        """An operation at a bay: the pallet stands there for the window; missions listed before
        the bay stay come first. A failed check runs the fail branch, then the check again."""
        op, rng = task.op, self.rng
        slot = self.slot_of[CARRIER[op.name]]
        label = self.label(op.name)
        d = self.draw(op)
        steps = list(op.evidence)
        bay_at = next((i for i, s in enumerate(steps) if s.activity == "bay_stay"), None)
        pre = [s for i, s in enumerate(steps) if s.activity == "mission" and bay_at is not None and i < bay_at]
        inside = [s for s in steps if s.activity == "mission" and s not in pre]
        raws, uses = [], []
        stay_s = 0.0
        if pre:
            m_raws, m_uses = _missions(pre, 0.0, 0.4 * d, op.name, rng)
            raws += m_raws
            uses += m_uses
            stay_s = 0.3 * d
        span = d - stay_s
        if inside:
            m_raws, m_uses = _missions(inside, stay_s + 0.15 * span, stay_s + 0.6 * span, op.name, rng)
            raws += m_raws
            uses += m_uses
        fail_ops = _fail_ops(self.recipe)
        can_fail = len(fail_ops) >= 2 and any(s.activity == "check_failed" for s in steps)
        fail = can_fail and not task.force_pass and self.fails < MAX_FAILS and rng.random() < self.fail_p
        result_t = stay_s + 0.8 * span
        margin = min(3.0, 0.1 * span)
        for step in steps:
            if step.activity == ("check_failed" if fail else "check_passed"):
                raws.append(_point(step, result_t, op.name))
            elif step.activity == "test_result":
                raws.append(_point(step, stay_s + 0.85 * span, op.name, result="pass"))
            elif step.activity in ("operation_started", "program_started"):
                raws.append(_point(step, stay_s + rng.uniform(0.3, margin), op.name))
            elif step.activity in ("operation_done", "program_ended"):
                raws.append(_point(step, d - rng.uniform(0.3, margin), op.name))
        for r in raws:
            r.task = label
        stay_e = end = d
        if fail:   # the removal starts at the bay: take missions while the pallet is there
            remove = fail_ops[0]
            m_steps = [s for s in remove.evidence if s.activity == "mission"]
            r_s = result_t + rng.uniform(3.0, 8.0)
            r_d = self.draw(remove)
            m_raws, m_uses = _missions(m_steps, r_s, r_s + r_d, remove.name, rng)
            remove_label = self.label(remove.name)
            for r in m_raws:
                r.task = remove_label
            raws += m_raws
            uses += m_uses
            takes = [u for u, st in zip(m_uses, m_steps) if st.attrs["mission"].endswith("_from_pallet")]
            if takes:
                stay_e = takes[-1][2] + rng.uniform(2.0, 6.0)
            end = r_s + r_d
        stay = _stay(bay, slot, stay_s, stay_e, op.name)
        stay.task = label
        raws.append(stay)
        uses.append((f"bay:{bay}", stay_s, stay_e))
        uses += [(res, stay_s, d) for res in sorted(op.resources) if res in STATIONS]
        t = self.cal.place(max(ready, self.slot_ready.get(slot, 0.0) - stay_s), uses)
        self.cal.book(t, uses)
        self.emit(raws, t)
        self.use_slot(slot, t + stay_e)
        if task.extra:
            for r in raws:
                r.extra = True
        if fail:
            self.fails += 1
            self.load([fail_ops[1]], t + end, None)
            self.station(task, self.slot_ready[self.slot_of[CARRIER[op.name]]], bay)
        else:
            self.done[task.key] = t + end

    def robot(self, task: Task, ready: float) -> None:
        """Missions only, after the last stay of the pallet (the delivery)."""
        op = task.op
        d = self.draw(op)
        steps = [s for s in op.evidence if s.activity == "mission"]
        raws, uses = _missions(steps, 0.0, d, op.name, self.rng)
        label = self.label(op.name)
        for r in raws:
            r.task = label
            r.extra = task.extra
        t = self.cal.place(ready, uses)
        self.cal.book(t, uses)
        self.emit(raws, t)
        slot = self.slot_of[CARRIER[op.name]]
        self.slot_end[slot] = max(self.slot_end.get(slot, 0.0), t + d)
        self.done[task.key] = t + d


def _plan(recipe: Recipe, kind: str | None, rng: random.Random) -> tuple[list[Task], dict | None]:
    """The tasks after the loading (main branch) and the structural deviation, if any."""
    main = [op for op in recipe.operations if op.branch == "main"]
    tasks = [Task(op.name, op, list(op.depends)) for op in main if not (_is_reserve(op) or _is_load(op))]
    by_key = {t.key: t for t in tasks}
    if kind == "skip":
        name = rng.choice(sorted(by_key))
        gone = by_key.pop(name)
        for t in by_key.values():
            if name in t.deps:
                t.deps = sorted((set(t.deps) - {name}) | set(gone.deps))
        return list(by_key.values()), {"kind": "skip", "operation": name}
    if kind == "swap":
        at_bay = {k for k, t in by_key.items() if _bay(t.op) is not None}
        pairs = [(a, b) for b in sorted(at_bay) for a in by_key[b].deps if a in at_bay]
        a, b = rng.choice(pairs)
        ta, tb = by_key[a], by_key[b]
        a_deps = list(ta.deps)
        tb.deps = sorted((set(tb.deps) - {a}) | set(a_deps))
        ta.deps = sorted(set(a_deps) | {b})
        for t in by_key.values():
            if b in t.deps and t is not ta:
                t.deps = sorted(set(t.deps) | {a})
        ta.force_pass = tb.force_pass = True
        return tasks, {"kind": "swap", "operation": a, "with": b}
    if kind == "extra":
        names = sorted(k for k, t in by_key.items()
                       if any(s.activity in ("check_passed", "test_result") for s in t.op.evidence))
        name = rng.choice(names)
        extra = Task(f"{name}:extra", by_key[name].op, [name], extra=True, force_pass=True)
        for t in by_key.values():
            if name in t.deps:
                t.deps = sorted(set(t.deps) | {extra.key})
        return tasks + [extra], {"kind": "extra", "operation": name}
    return tasks, None


def _order(run: OrderRun, arrival: float, kind: str | None) -> dict | None:
    recipe, rng = run.recipe, run.rng
    main = [op for op in recipe.operations if op.branch == "main"]
    reserve = next((op.name for op in main if _is_reserve(op)), None)
    loads = [op for op in main if _is_load(op)]
    if len(loads) > 1 and rng.random() < 0.5:
        loads = loads[::-1]                        # the loads are concurrent in the recipe
    tasks, dev = _plan(recipe, kind, rng)
    run.load(loads, arrival, reserve)
    seq = {op.name: op.sequence for op in recipe.operations}
    pending = {t.key: t for t in tasks}
    while pending:
        task = min((t for t in pending.values() if all(d in run.done for d in t.deps)),
                   key=lambda t: (seq[t.op.name], t.extra, t.key))
        del pending[task.key]
        ready = max(run.done[d] for d in task.deps)
        bay = _bay(task.op)
        if bay is None:
            run.robot(task, ready + rng.uniform(5.0, 15.0))
        else:
            run.station(task, ready, bay)
    return dev


def _post(raws: list[Raw], kind: str, rng: random.Random, next_seq, anchors: set[str]) -> dict:
    """Deviations on the events of one finished order: stuck, gap, duplicate.
    `anchors` are the operations of the first loading: they are never stuck."""
    if kind == "stuck":   # an operation starts and never ends; the order stops there
        groups = defaultdict(list)
        for r in raws:
            groups[r.task].append(r)
        name = rng.choice(sorted(k for k, g in groups.items() if len(g) >= 2 and g[0].op not in anchors))
        first = min(groups[name], key=lambda r: (r.time, r.seq))
        raws[:] = [r for r in raws if (r.time, r.seq) <= (first.time, first.seq)]
        return {"kind": "stuck", "operation": first.op, "raws": [first]}
    if kind == "gap":     # a sensor gap: one event is missing
        r = rng.choice([r for r in raws if r.activity != "bay_stay"])
        raws.remove(r)
        return {"kind": "gap", "operation": r.op, "raws": [],
                "removed": {"activity": r.activity, "resource": r.resource, "time": round(r.time, ROUND)}}
    # duplicate: one event recorded twice (not a mission: a robot does one mission at a time)
    r = rng.choice([r for r in raws if not r.activity.startswith("mission_")])
    copy = Raw(r.activity, r.resource, r.time, dict(r.attrs), r.op, r.task, r.slot, r.pallet, next_seq())
    raws.append(copy)
    return {"kind": "duplicate", "operation": r.op, "raws": [r, copy]}


def _finish(raws: list[Raw]) -> tuple[list[Event], dict[int, str]]:
    """Round the times, sort by (time, creation), give ids e1.. in that order."""
    for r in raws:
        r.time = round(r.time, ROUND)
        if r.activity == "bay_stay":
            r.attrs["start"] = round(r.attrs["start"], ROUND)
    raws.sort(key=lambda r: (r.time, r.seq))
    ids = {id(r): f"e{i}" for i, r in enumerate(raws, 1)}
    events = [Event(ids[id(r)], r.activity, r.resource, r.time, r.pallet, CLAIM[r.activity], r.attrs, ())
              for r in raws]
    return events, ids


def _ids(raws: list[Raw], ids: dict[int, str]) -> list[str]:
    return sorted((ids[id(r)] for r in raws), key=lambda i: int(i[1:]))


def _truth(raws: list[Raw], ids: dict[int, str], recipe: str, dev: dict | None, pallets: list[int]) -> dict:
    own = [r for r in raws if not r.extra]
    groups: dict[str, list[Raw]] = defaultdict(list)
    for r in own:
        groups[r.task].append(r)
    operations = sorted(({"name": g[0].op, "event_ids": _ids(g, ids)} for g in groups.values()),
                        key=lambda o: int(o["event_ids"][0][1:]))
    devs = []
    if dev is not None:
        d = {k: v for k, v in dev.items() if k != "raws"}
        if dev["kind"] == "extra":
            d["event_ids"] = _ids([r for r in raws if r.extra], ids)
        elif dev["kind"] == "swap":
            d["event_ids"] = _ids([r for r in own if r.op in (dev["operation"], dev["with"])], ids)
        else:
            d["event_ids"] = _ids(dev.get("raws", []), ids)
        devs.append(d)
    return {"recipe": recipe, "event_ids": _ids(own, ids), "deviations": devs,
            "operations": operations, "pallets": pallets}


def simulate(recipes: dict[str, Recipe], *, orders: int, seed: int, mix: dict[str, float],
             fail_p: float, deviations: dict[str, float]) -> tuple[list[Event], dict]:
    """Play `orders` orders out. Returns the events (ids in time order) and the truth:
    {"orders": {"order:<n>": {"recipe", "event_ids", "deviations": [{"kind", "operation", "event_ids", ...}],
    "operations": [{"name", "event_ids"}], "pallets"}}}. At most one deviation per order;
    `deviations[kind]` is the probability of each kind."""
    rng = random.Random(seed)
    cal = Calendar()
    pallet_free = {p: 0.0 for p in PALLETS}
    names = sorted(mix)
    counter = iter(range(1, 10**9))

    def next_seq() -> int:
        return next(counter)

    arrival = 0.0
    all_raws: list[Raw] = []
    per_order = []
    for n in range(1, orders + 1):
        arrival += rng.expovariate(1.0 / MEAN_GAP_S)
        recipe = recipes[rng.choices(names, weights=[mix[k] for k in names])[0]]
        u, kind, acc = rng.random(), None, 0.0
        for k in KINDS:
            acc += deviations.get(k, 0.0)
            if u < acc:
                kind = k
                break
        run = OrderRun(recipe, rng, cal, pallet_free, fail_p)
        dev = _order(run, arrival, kind if kind in ("skip", "swap", "extra") else None)
        for r in run.raws:
            r.seq = next_seq()
        for slot, pallet in run.pallet_of.items():   # back to the pool after its last use
            pallet_free[pallet] = run.slot_end[slot] + rng.uniform(*TRANSIT_S)
        if kind in ("stuck", "gap", "duplicate"):
            anchors = {op.name for op in recipe.operations if _is_reserve(op) or _is_load(op)}
            dev = _post(run.raws, kind, rng, next_seq, anchors)
        all_raws += run.raws
        per_order.append((f"order:{n}", recipe.name, run.raws, dev, sorted(set(run.pallet_of.values()))))
    events, ids = _finish(all_raws)
    truth = {"orders": {oid: _truth(raws, ids, name, dev, pallets)
                        for oid, name, raws, dev, pallets in per_order}}
    return events, truth


# --- the reference order ----------------------------------------------------
# One gadget order with the shape measured on the lab recording (ruling R3):
# pallet 9 carries the board, pallet 7 the covers that fail the check,
# pallet 8 the new covers. The recording ends while the engrave runs: the mill
# bay stay is still open, so its bay_stay event has attrs.open = true and the
# time of the end of the recording. Names come from the recipe evidence.

REF_END_S = 1118.0
REF_STUCK_END_S = 1400.0
REF_CUT_S = 250.0


def _ref_raws(recipe: Recipe, end: float) -> list[Raw]:
    ops = {op.name: op for op in recipe.operations}
    raws: list[Raw] = []

    def missions(op: str, times: list[tuple[float, float]], task: str | None = None) -> None:
        steps = [s for s in ops[op].evidence if s.activity == "mission"]
        assert len(steps) == len(times), op
        for step, (s, e) in zip(steps, times):
            for r in _mission(step, s, e, op):
                r.task = task or op
                raws.append(r)

    def stay(op: str, bay: str, pallet: int, s: float, e: float, task: str | None = None, **extra: Any) -> None:
        r = _stay(bay, None, s, e, op, **extra)
        r.pallet, r.task = pallet, task or op
        raws.append(r)

    def point(op: str, activity: str, t: float, task: str | None = None, **extra: Any) -> None:
        step = next(s for s in ops[op].evidence if s.activity == activity)
        r = _point(step, t, op, **extra)
        r.task = task or op
        raws.append(r)

    missions("load_board", [(41.0, 150.4), (152.1, 233.6)])
    stay("reserve_pallet", "load", 9, 209.0, 228.0)
    missions("load_covers", [(235.2, 259.8), (261.0, 281.5), (282.6, 329.8), (331.0, 376.4)])
    stay("load_covers", "load", 7, 284.0, 371.0)
    stay("test_board", "tester", 9, 304.0, 378.0)
    point("test_board", "test_result", 371.2, result="pass")
    missions("check_covers", [(380.5, 391.2)], "check_covers#1")
    stay("check_covers", "qc", 7, 392.0, 523.0, "check_covers#1")
    point("check_covers", "check_failed", 398.1, "check_covers#1")
    stay("buffer_board", "assembly", 9, 395.0, 417.0)
    missions("bin_covers", [(404.0, 455.3), (456.6, 515.9), (517.2, 548.0), (549.1, 580.6), (582.0, 613.0)])
    missions("reload_covers", [(406.0, 470.5), (471.8, 540.2), (541.5, 628.4), (629.7, 683.9)])
    stay("reload_covers", "load", 8, 588.0, 678.0)
    missions("check_covers", [(688.3, 699.6)], "check_covers#2")
    stay("check_covers", "qc", 8, 702.0, 711.0, "check_covers#2")
    point("check_covers", "check_passed", 708.2, "check_covers#2")
    stay("assemble_gadget", "assembly", 8, 744.0, 883.0)
    for n, (s, e) in enumerate([(748.5, 779.0), (781.2, 811.6), (813.0, 846.4), (848.1, 879.3)], 1):
        point("assemble_gadget", "operation_started", s, part=n)
        point("assemble_gadget", "operation_done", e, part=n)
    point("engrave_gadget", "program_started", 918.0)
    stay("engrave_gadget", "mill", 8, 918.0, end, open=True)
    for seq, r in enumerate(raws, 1):
        r.seq = seq
    return raws


def _ref_log(name: str, raws: list[Raw], injected: list[dict], devs: list[dict]) -> tuple[dict, list[Event]]:
    events, ids = _finish(raws)
    order = _truth(raws, ids, "gadget", None, sorted({r.pallet for r in raws if r.pallet is not None}))
    order["deviations"] = [{**{k: v for k, v in d.items() if k != "raws"}, "event_ids": _ids(d.get("raws", []), ids)}
                           for d in devs]
    return {"log": name, "injected": injected, "orders": {"order:1": order}}, events


def reference_logs(recipes: dict[str, Recipe]) -> dict[str, tuple[dict, list[Event]]]:
    """ref-order and its injected copies: name -> (header, events). Each header has the
    injected faults and the order truth. Fixed times, no randomness."""
    gadget = recipes["gadget"]
    out = {"ref-order": _ref_log("ref-order", _ref_raws(gadget, REF_END_S), [], [])}

    raws = _ref_raws(gadget, REF_STUCK_END_S)      # the engrave never ends; recorded to t=1400
    start = next(r for r in raws if r.op == "engrave_gadget" and r.activity == "signal_changed")
    fault = {"kind": "stuck", "operation": "engrave_gadget"}
    out["ref-stuck"] = _ref_log("ref-stuck", raws, [fault], [{**fault, "raws": [start]}])

    raws = [r for r in _ref_raws(gadget, REF_END_S) if r.task != "check_covers#2"]   # the second check is skipped
    fault = {"kind": "skip", "operation": "check_covers"}
    out["ref-skip-check"] = _ref_log("ref-skip-check", raws, [fault], [dict(fault)])

    raws = _ref_raws(gadget, REF_END_S)            # one mission end is missing (a sensor gap)
    gone = next(r for r in raws if r.activity == "mission_ended" and r.attrs["mission"] == "drop_covers_in_bin")
    raws.remove(gone)
    fault = {"kind": "gap", "operation": "bin_covers", "activity": "mission_ended", "mission": "drop_covers_in_bin"}
    out["ref-no-end"] = _ref_log("ref-no-end", raws, [fault], [dict(fault)])

    raws = [r for r in _ref_raws(gadget, REF_END_S) if r.time <= REF_CUT_S]   # before the divergence
    out["ref-prefix"] = _ref_log("ref-prefix", raws, [{"kind": "cut", "time": REF_CUT_S}], [])
    return out
