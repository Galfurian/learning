import math

import pandas as pd

from pmlab.checks import run_checks
from pmlab.log import Entry, Trace
from pmlab.reference import pm4py

N = [0]


def trace(case, ops):
    """ops: (activity, start, complete or None)."""
    entries = []
    for activity, start, end in ops:
        N[0] += 1
        entries.append(Entry(case, activity, "start", start, "r", (case,), (f"e{N[0]}",), "inferred"))
        if end is not None:
            entries.append(Entry(case, activity, "complete", end, "r", (case,), (f"e{N[0]}",), "inferred"))
    return Trace(case, sorted(entries, key=lambda e: (e.time, e.lifecycle != "start")))


# load_board depends on reserve_pallet, test_board on load_board (data/recipes.yaml).
TRACES = [
    trace("order:1", [("reserve_pallet", 0, 10), ("load_board", 12, 112), ("test_board", 120, 190)]),
    trace("order:2", [("reserve_pallet", 0, 20), ("load_board", 25, 145), ("test_board", 150, 230)]),
    trace("order:3", [("reserve_pallet", 0, 15), ("load_board", 16, 96), ("test_board", 100, None)]),
]


def checks(exe, check):
    done, stats = check.calls(exe.performance, TRACES)
    if not done:
        return
    r, lb, tb = (stats.get(a) for a in ("reserve_pallet", "load_board", "test_board"))
    check.ok(r is not None and (r.count, r.p50, r.p95, r.max) == (3, 15, 20, 20),
             "reserve_pallet: service 10, 20, 15 s -> p50 15, p95 20 (nearest rank)", r)
    check.ok(r is not None and math.isnan(r.wait_p50), "reserve_pallet depends on nothing: no waiting sample", r)
    check.ok(lb is not None and (lb.p50, lb.p95, lb.wait_p50, lb.wait_p95) == (100, 120, 2, 5),
             "load_board: service p50 100, p95 120; waiting after reserve_pallet p50 2, p95 5", lb)
    check.ok(tb is not None and (tb.count, tb.p50, tb.p95) == (2, 70, 80),
             "test_board: a start with no complete is no sample", tb)
    check.ok(tb is not None and (tb.wait_p50, tb.wait_p95) == (5, 8), "test_board waits 8 s and 5 s", tb)

    # pm4py: the same maximum service time per activity, on the same intervals.
    rows = []
    for t in TRACES:
        starts = {}
        for e in t.entries:
            if e.lifecycle == "start":
                starts[e.activity] = e.time
            else:
                rows.append({"case:concept:name": t.case_id, "concept:name": e.activity,
                             "start_timestamp": pd.Timestamp(starts.pop(e.activity), unit="s"),
                             "time:timestamp": pd.Timestamp(e.time, unit="s")})
    ref = pm4py.get_service_time(pd.DataFrame(rows), aggregation_measure="max", start_timestamp_key="start_timestamp")
    check.ok({a: stats[a].max for a in ref} == {a: float(v) for a, v in ref.items()},
             "the same maximum service times as pm4py.get_service_time", ref)


run_checks(checks, __file__.replace("check.py", "exe08.py"))
