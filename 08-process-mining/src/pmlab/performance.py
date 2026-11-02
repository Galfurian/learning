"""Performance baselines per operation, and open operations at a time `now`."""

import math
from collections import defaultdict
from dataclasses import dataclass

from pmlab.abstraction import operations_by_name
from pmlab.log import Entry, Trace
from pmlab.recipes import Recipe, load_recipes


@dataclass(frozen=True)
class Stats:
    count: int          # number of service samples
    p50: float
    p95: float
    max: float
    wait_p50: float
    wait_p95: float


@dataclass(frozen=True)
class Open:
    activity: str
    start: float
    age: float
    verdict: str        # "running" | "unusual"
    p95: float
    nominal_s: float
    source_ids: tuple[str, ...]


def _percentile(values: list[float], q: float) -> float:
    """Nearest-rank percentile; nan for no values."""
    if not values:
        return math.nan
    ordered = sorted(values)
    rank = max(1, math.ceil(q * len(ordered)))
    return ordered[rank - 1]


def _pairs(entries: list[Entry]) -> dict[str, list[tuple[Entry, Entry]]]:
    """Per activity, each start with its own next complete, in time order."""
    pending: dict[str, Entry] = {}
    out: dict[str, list[tuple[Entry, Entry]]] = defaultdict(list)
    for e in entries:
        if e.lifecycle == "start":
            pending[e.activity] = e
        elif e.activity in pending:
            out[e.activity].append((pending.pop(e.activity), e))
    return out


def performance(traces: list[Trace]) -> dict[str, Stats]:
    """Service and waiting time per operation.

    Service = complete - start. Waiting = start - the latest complete, in the
    same case, of the operation's dependencies that occur before the start.
    The case recipe is unknown, so dependencies come from the operation union
    over all recipes. With no such dependency, the start has no waiting sample.
    """
    ops = operations_by_name(load_recipes())
    service: dict[str, list[float]] = defaultdict(list)
    wait: dict[str, list[float]] = defaultdict(list)
    for trace in traces:
        for activity, pairs in _pairs(trace.entries).items():
            depends = ops[activity].depends if activity in ops else ()
            for start, complete in pairs:
                service[activity].append(complete.time - start.time)
                done = [e.time for e in trace.entries
                        if e.lifecycle == "complete" and e.activity in depends and e.time <= start.time]
                if done:
                    wait[activity].append(start.time - max(done))
    return {
        a: Stats(len(s), _percentile(s, 0.5), _percentile(s, 0.95), max(s),
                 _percentile(wait[a], 0.5), _percentile(wait[a], 0.95))
        for a, s in service.items()
    }


def open_operations(trace: Trace, now: float, stats: dict[str, Stats], recipe: Recipe) -> list[Open]:
    """Operations started and not completed by `now`; later entries do not exist.

    Verdict is "unusual" if the age is over the p95 service time of the
    operation, else "running". An operation with no stats uses nominal_s * 1.5
    as p95.
    """
    nominal = {op.name: op.nominal_s for op in recipe.operations}
    seen = [e for e in trace.entries if e.time <= now]
    last: dict[str, Entry] = {}
    for e in seen:
        if e.lifecycle == "start":
            last[e.activity] = e
        elif last.get(e.activity) is not None and last[e.activity].lifecycle == "start":
            last[e.activity] = e
    out = []
    for activity, e in last.items():
        if e.lifecycle != "start":
            continue
        nom = nominal.get(activity, math.nan)
        p95 = stats[activity].p95 if activity in stats else nom * 1.5
        age = now - e.time
        out.append(Open(activity, e.time, age, "unusual" if age > p95 else "running", p95, nom, e.source_ids))
    return sorted(out, key=lambda o: o.start)
