import json
import subprocess
import sys
from pathlib import Path

import pytest

from pmlab.events import read_events
from pmlab.recipes import UNIT_ROOT, load_recipes
from test_simulate import assert_exclusive, assert_truth_covers

DATA = UNIT_ROOT / "data"
LOGS = ("train", "holdout")
REFS = ("ref-order", "ref-stuck", "ref-skip-check", "ref-no-end", "ref-prefix")
RECIPES = load_recipes()


def log(name):
    return read_events(DATA / "logs" / f"{name}.jsonl")


def truth(name):
    return json.loads((DATA / "logs" / f"{name}.truth.json").read_text(encoding="utf-8"))


def ref(name):
    return read_events(DATA / "orders" / f"{name}.jsonl")


def spans(events, t):
    by_id = {e.event_id: e for e in events}
    return {oid: (min(by_id[i].time for i in o["event_ids"]), max(by_id[i].time for i in o["event_ids"]))
            for oid, o in t["orders"].items() if o["event_ids"]}


def test_committed_data_current(tmp_path):
    subprocess.run([sys.executable, str(DATA / "build.py"), "--out", str(tmp_path)], check=True, cwd=UNIT_ROOT)
    built = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*") if p.is_file())
    assert built == sorted(
        [Path("logs") / f"{n}{s}" for n in LOGS for s in (".jsonl", ".truth.json")]
        + [Path("orders") / f"{n}.jsonl" for n in REFS]
    )
    for rel in built:
        assert (tmp_path / rel).read_bytes() == (DATA / rel).read_bytes(), rel


@pytest.mark.parametrize("name,orders", [("train", 200), ("holdout", 60)])
def test_logs_match_truth(name, orders):
    header, events = log(name)
    t = truth(name)
    assert header["log"] == name and header["truth"] == f"{name}.truth.json"
    assert len(t["orders"]) == orders
    assert_truth_covers(events, t)
    assert_exclusive(events)


def test_overlap_and_reuse():
    _, events = log("train")
    t = truth("train")
    span = spans(events, t)
    ordered = sorted(span.items(), key=lambda kv: kv[1])
    overlapping = set()
    for (a, (s1, e1)), (b, (s2, e2)) in zip(ordered, ordered[1:]):
        if s2 < e1:
            overlapping |= {a, b}
    assert len(overlapping) >= 0.2 * len(span)
    by_id = {e.event_id: e for e in events}
    pallet_orders = {}
    for oid, o in t["orders"].items():
        for i in o["event_ids"]:
            if by_id[i].pallet is not None:
                pallet_orders.setdefault(by_id[i].pallet, set()).add(oid)
    assert set(pallet_orders) <= set(range(1, 11))
    assert any(len(orders) >= 2 for orders in pallet_orders.values())


def test_logs_small():
    size = sum(p.stat().st_size for p in (DATA / "logs").iterdir())
    assert size < 3_000_000


def test_ref_order_shape():
    header, events = ref("ref-order")
    assert header["log"] == "ref-order" and header["injected"] == []
    assert list(header["orders"]) == ["order:1"]
    assert header["orders"]["order:1"]["recipe"] == "gadget"
    assert header["orders"]["order:1"]["event_ids"] == [e.event_id for e in events]
    assert {e.pallet for e in events if e.pallet is not None} == {7, 8, 9}
    checks = [e.activity for e in events if e.activity.startswith("check_")]
    assert checks == ["check_failed", "check_passed"]
    assert sum(1 for e in events if e.activity == "operation_done" and e.resource == "assembly_cell") == 4
    assert abs(events[-1].time - 1118) <= 1
    deliver = {s.attrs["mission"] for s in next(o for o in RECIPES["gadget"].operations
                                                 if o.name == "deliver_gadget").evidence}
    assert not any(e.attrs.get("mission") in deliver for e in events)
    engrave = [e for e in events if e.activity == "signal_changed"]
    assert [(e.time, e.attrs["new"]) for e in engrave] == [(918.0, True)]
    assert_exclusive(events)


def test_ref_measured_times():
    _, events = ref("ref-order")
    stays = {(e.pallet, e.attrs["bay"]): (e.attrs["start"], e.time) for e in events if e.activity == "bay_stay"}
    assert stays[(9, "load")] == (209.0, 228.0)
    assert stays[(9, "tester")] == (304.0, 378.0)
    assert stays[(7, "load")] == (284.0, 371.0)
    assert stays[(7, "qc")] == (392.0, 523.0)
    assert stays[(8, "load")] == (588.0, 678.0)
    assert stays[(8, "qc")] == (702.0, 711.0)
    assert stays[(8, "assembly")] == (744.0, 883.0)
    assert stays[(8, "mill")][0] == 918.0


def test_ref_variants():
    _, base = ref("ref-order")
    expect = {
        "ref-stuck": ("stuck", "engrave_gadget"),
        "ref-skip-check": ("skip", "check_covers"),
        "ref-no-end": ("gap", "bin_covers"),
        "ref-prefix": ("cut", None),
    }
    for name, (kind, operation) in expect.items():
        header, events = ref(name)
        assert header["log"] == name
        assert [(d["kind"], d.get("operation")) for d in header["injected"]] == [(kind, operation)]
        assert header["orders"]["order:1"]["event_ids"] == [e.event_id for e in events]
        assert [e.event_id for e in events] == [f"e{i}" for i in range(1, len(events) + 1)]
    _, stuck = ref("ref-stuck")
    assert stuck[-1].time == 1400.0
    assert not any(e.activity == "signal_changed" and e.attrs["new"] is False for e in stuck)
    _, skip = ref("ref-skip-check")
    assert [e.activity for e in skip if e.activity.startswith("check_")] == ["check_failed"]
    _, no_end = ref("ref-no-end")
    assert len(no_end) == len(base) - 1
    assert sum(e.activity == "mission_started" for e in no_end) == sum(e.activity == "mission_ended" for e in no_end) + 1
    _, prefix = ref("ref-prefix")
    assert prefix and max(e.time for e in prefix) <= 250
    assert not any(e.attrs.get("bay") == "qc" or e.resource == "tester" for e in prefix)
