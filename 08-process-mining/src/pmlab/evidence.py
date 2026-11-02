"""Evidence lines: what the process mining says about one order at a time `now`.

    log -> derive_extra -> correlate -> abstract -> to_log -> per order:
        recipe candidates (monitor) + open operations (performance)
        + alignment moves (align) + coverage -> numbered lines

Each line starts with the event ids it rests on, in square brackets, and ends
with its claim kind in parentheses:

    inferred   more than one recipe still fits: the recipe is not known
    derived    computed from the entries (recipe, open operation, moves)
    coverage   what the log does not show (unmapped activities, causes)

There is no cause line in this unit: the log shows what ran and when, not why.
"""

from dataclasses import dataclass, field
from functools import cache
from pathlib import Path

from pmlab.abstraction import abstract
from pmlab.align import align
from pmlab.compile import compile_recipe
from pmlab.events import Event, read_events
from pmlab.log import Entry, Trace, to_log
from pmlab.monitor import candidates, prefix_at, status
from pmlab.orders import correlate
from pmlab.performance import Open, Stats, performance
from pmlab.petri import Net
from pmlab.recipes import UNIT_ROOT, Recipe, load_recipes
from pmlab.rules import derive_extra

BASELINE = "train"
FAIL_OPS = ("bin_covers", "reload_covers")
NO_CAUSE = ("no line gives a cause: the recording does not show why an operation is slow or why a check failed "
            "(coverage)")


@dataclass
class Mined:
    name: str
    recipes: dict[str, Recipe]
    traces: dict[str, Trace]           # order id -> trace
    nets: dict[str, Net]
    stats: dict[str, Stats]            # baseline: the train log
    fail_rate: tuple[int, int]         # (check_covers completes, failed ones) over the train log
    events: list[Event] = field(default_factory=list)
    orders: dict[str, str] = field(default_factory=dict)    # event id -> order id
    entries: list[Entry] = field(default_factory=list)


@dataclass
class Finding:
    order: str
    now: float
    recipes: list[str]                 # candidates; empty if no recipe fits (or no order)
    open: list[Open]
    moves: list[tuple[str, str]]       # non-sync moves (kind, activity), unmapped left out
    lines: list[str]


def log_path(name: str) -> Path:
    """`train` and `holdout` are simulated logs; `ref-*` are copies of the reference order."""
    folder = "orders" if name.startswith("ref-") else "logs"
    return UNIT_ROOT / "data" / folder / f"{name}.jsonl"


@cache
def _baseline() -> tuple[dict[str, Stats], tuple[int, int]]:
    _, _, _, traces = _mine(BASELINE)
    return performance(traces), fail_rate(traces)


@cache
def _mine(name: str) -> tuple[list[Event], dict[str, str], list[Entry], list[Trace]]:
    _, events = read_events(log_path(name))
    events = derive_extra(events)
    orders = correlate(events, load_recipes())
    entries = abstract(events, load_recipes(), orders)
    return events, orders, entries, to_log(entries)


def failed_checks(activities) -> list[int]:
    """Indexes of the check_covers that failed: a bin_covers follows before the next check_covers."""
    out, check = [], None
    for i, a in enumerate(activities):
        if a == "check_covers":
            check = i
        elif a == "bin_covers" and check is not None:
            out.append(check)
            check = None
    return out


def fail_rate(traces: list[Trace]) -> tuple[int, int]:
    """(check_covers completes, failed ones) over the traces."""
    return (sum(t.activities.count("check_covers") for t in traces),
            sum(len(failed_checks(t.activities)) for t in traces))


@cache
def pipeline(log_name: str) -> Mined:
    """The mined log, cached per name. Order ids are the found ids ("order:N")."""
    events, orders, entries, traces = _mine(log_name)
    recipes = load_recipes()
    stats, rate = _baseline()
    return Mined(log_name, recipes, {t.case_id: t for t in traces},
                 {n: compile_recipe(r) for n, r in recipes.items()}, stats, rate, events, orders, entries)


def _t(x: float) -> str:
    return f"{x:.1f}".rstrip("0").rstrip(".")


def _ids(ids) -> str:
    return "[" + ", ".join(ids) + "] " if ids else ""


def _known(nets: dict[str, Net]) -> set[str]:
    return {lab for net in nets.values() for lab in net.transitions.values() if lab is not None}


def _or(names: list[str]) -> str:
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " or " + names[-1]


def _deciding_entry(prefix: Trace, nets: dict[str, Net], ids: tuple[str, ...]) -> Entry | None:
    """The entry after which one recipe was left (start and complete share their ids)."""
    for i, e in enumerate(prefix.entries):
        if e.source_ids == ids and len(candidates(Trace(prefix.case_id, prefix.entries[:i + 1]), nets).recipes) == 1:
            return e
    return None


def _recipe_line(order: str, prefix: Trace, nets: dict[str, Net], cands, last: Entry | None) -> str:
    if len(cands.recipes) == 1:
        (name,) = cands.recipes
        e = _deciding_entry(prefix, nets, cands.deciding_ids)
        how = f": only {name} fits {e.activity} ({e.lifecycle}) at t={_t(e.time)} s" if e else ""
        return f"{_ids(cands.deciding_ids)}{order} follows recipe {name}{how} (derived)"
    if not cands.recipes:
        return f"{order} fits no recipe exactly: see the deviations (derived)"
    where = f"up to {last.activity} at t={_t(last.time)} s, " if last else "with no completed operation, "
    deciding = "; ".join(f"{a} would decide {_or(rs)}" for a, rs in cands.deciding.items())
    return (f"{_ids(last.source_ids if last else ())}{where}{order} can still be {_or(cands.recipes)}: "
            f"the recipes share these steps, the recipe is not decided yet; {deciding} (inferred)")


def _open_line(o: Open, order: str, now: float, stats: dict[str, Stats]) -> str:
    base = (f"usual time p50 {_t(stats[o.activity].p50)} s, p95 {_t(o.p95)} s over the train log"
            if o.activity in stats else f"no baseline, p95 taken as 1.5 x nominal = {_t(o.p95)} s")
    verdict = "unusual: longer than the p95" if o.verdict == "unusual" else "running: within the p95"
    return (f"{_ids(o.source_ids)}{order} is at {o.activity}: started at t={_t(o.start)} s, still open at "
            f"t={_t(now)} s, age {_t(o.age)} s; {base}; nominal {_t(o.nominal_s)} s; {verdict} (derived)")


def _move_lines(order: str, recipe: str, moves, running: bool) -> list[str]:
    out, before = [], None
    for mv in moves:
        if mv.kind == "sync":
            before = mv
            continue
        if mv.kind == "log":
            out.append(f"{_ids(mv.source_ids)}{order} has {mv.activity} where recipe {recipe} does not have it: "
                       f"extra (log move) (derived)")
        else:
            after = f" after {before.activity}" if before else " at the start"
            out.append(f"{_ids(before.source_ids if before else ())}recipe {recipe} has {mv.activity}{after}; "
                       f"{order} does not have it: skipped (model move) (derived)")
    if not out:
        # The verdict covers every entry; it cites the first and the last one, so it can be cited.
        sync = [mv for mv in moves if mv.kind == "sync"]
        ids = [sync[0].source_ids[0], sync[-1].source_ids[0]] if sync else []
        so_far = " so far" if running else ""
        out.append(f"{_ids(list(dict.fromkeys(ids)))}{order} follows recipe {recipe}{so_far} with no deviation "
                   f"(alignment cost 0) (derived)")
    return out


def _fail_lines(order: str, moves, rate: tuple[int, int]) -> list[str]:
    """The fail branch, when the alignment has it as sync moves. One id per entry."""
    sync = [mv for mv in moves if mv.kind == "sync"]
    failed = failed_checks([mv.activity for mv in sync])
    if not failed:
        return []
    ids = [mv.source_ids[0] for i, mv in enumerate(sync) if i in failed or mv.activity in FAIL_OPS]
    checks, fails = rate
    times = "once" if len(failed) == 1 else f"{len(failed)} times"
    return [f"{_ids(ids)}{order}: check_covers failed {times}, then bin_covers and reload_covers ran: "
            f"fail branch of the recipe: conformant (derived)",
            f"over the train log, check_covers failed {fails} of {checks} times ({100 * fails / checks:.0f}%) "
            f"(derived)"]


def mine(m: Mined, order: str, now: float) -> Finding:
    """Candidates, open operations, moves and the evidence lines of an order at `now`."""
    trace = m.traces.get(order)
    if trace is None:
        return Finding(order, now, [], [], [], [f"{order} is not in the log {m.name} (derived)"])
    prefix = prefix_at(trace, now)
    if not prefix.entries:
        return Finding(order, now, [], [], [], [f"{order} has no entry before t={_t(now)} s (derived)"])
    known = _known(m.nets)
    seen = Trace(order, [e for e in prefix.entries if e.activity in known])
    st = status(seen, now, m.nets, m.recipes, m.stats)
    cands = st.candidates
    done = [e for e in seen.entries if e.lifecycle == "complete"]
    last = done[-1] if done else None
    running = bool(st.open) or len(prefix.entries) < len(trace.entries)

    lines = [_recipe_line(order, seen, m.nets, cands, last)]
    lines += [_open_line(o, order, now, m.stats) for o in st.open]
    if not st.open and last is not None:
        if not running and st.remaining_s == 0:
            lines.append(f"{_ids(last.source_ids)}{order} is finished: its last operation {last.activity} "
                         f"completed at t={_t(last.time)} s (derived)")
        elif not running:
            lines.append(f"{_ids(last.source_ids)}{order} has no open operation and no later entry: its last "
                         f"completed operation is {last.activity} at t={_t(last.time)} s (derived)")
        else:
            nxt = f"; next in the recipe: {_or(st.next)}" if st.next else ""
            lines.append(f"{_ids(last.source_ids)}{order} has no open operation at t={_t(now)} s; its last "
                         f"completed operation is {last.activity} at t={_t(last.time)} s{nxt} (derived)")

    moves: list[tuple[str, str]] = []
    if len(cands.recipes) <= 1 or not running:   # while undecided, every candidate fits so far
        names = cands.recipes or sorted(m.nets)
        best, recipe = min(((align(m.nets[n], seen, complete=not running), n) for n in names),
                           key=lambda x: (x[0].cost, x[1]))
        moves = [(mv.kind, mv.activity) for mv in best.moves if mv.kind != "sync"]
        lines += _move_lines(order, recipe, best.moves, running)
        lines += _fail_lines(order, best.moves, m.fail_rate)

    for e in prefix.entries:
        if e.activity not in known:
            lines.append(f"{_ids(e.source_ids)}{order} has {e.activity} at t={_t(e.time)} s: it matches no "
                         f"recipe operation, so conformance ignores it (coverage)")
    lines.append(NO_CAUSE)
    return Finding(order, now, list(cands.recipes), list(st.open), moves, lines)


def evidence_lines(m: Mined, order: str, now: float) -> list[str]:
    return mine(m, order, now).lines
