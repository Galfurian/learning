from collections import Counter

import pytest

from pmlab.recipes import load_recipes
from pmlab.simulate import KINDS, simulate

RECIPES = load_recipes()
MIX = {"gadget": 0.5, "parts_test": 0.3, "brick_demo": 0.2}
ROBOTS = {"robot_a", "robot_b"}
CELL_BAY = {"assembly_cell": "assembly", "mill_cell": "mill"}


def run(seed=1, orders=30, p=0.0, fail_p=0.3):
    params = {"orders": orders, "seed": seed, "mix": MIX, "fail_p": fail_p,
              "deviations": {kind: p for kind in KINDS}}
    return simulate(RECIPES, **params)


def mission_intervals(events):
    """Started/ended pairs per robot. A start while another is open drops the open one (a gap)."""
    out, open_ = [], {}
    for e in sorted(events, key=lambda e: (e.time, int(e.event_id[1:]))):
        if e.activity == "mission_started":
            open_[e.resource] = e
        elif e.activity == "mission_ended":
            start = open_.pop(e.resource, None)
            if start is not None and start.attrs["mission"] == e.attrs["mission"]:
                out.append((e.resource, start.time, e.time))
    return out


def assert_exclusive(events):
    by_robot = {}
    for robot, s, e in mission_intervals(events):
        by_robot.setdefault(robot, []).append((s, e))
    for robot, spans in by_robot.items():
        spans.sort()
        for (s1, e1), (s2, e2) in zip(spans, spans[1:]):
            assert s2 >= e1, (robot, (s1, e1), (s2, e2))


def assert_truth_covers(events, truth):
    seen = Counter()
    for order in truth["orders"].values():
        seen.update(order["event_ids"])
        for dev in order["deviations"]:
            if dev["kind"] == "extra":
                seen.update(dev["event_ids"])
    ids = [e.event_id for e in events]
    assert len(ids) == len(set(ids))
    assert set(seen) == set(ids)
    assert all(n == 1 for n in seen.values()), [i for i, n in seen.items() if n > 1][:5]


def test_deterministic():
    a, truth_a = run(seed=3)
    b, truth_b = run(seed=3)
    c, _ = run(seed=4)
    assert a == b and truth_a == truth_b
    assert a != c


def test_ids_in_time_order():
    events, _ = run(p=0.05)
    assert [e.event_id for e in events] == [f"e{i}" for i in range(1, len(events) + 1)]
    assert [e.time for e in events] == sorted(e.time for e in events)


def test_no_order_id():
    events, _ = run(p=0.05)
    assert events
    for e in events:
        assert "order" not in e.attrs
        assert not any("order" in key for key in e.attrs)


def test_resource_exclusive():
    events, _ = run(orders=40, p=0.05)
    assert_exclusive(events)


def test_truth_covers_events():
    events, truth = run(orders=60, p=0.1)
    assert_truth_covers(events, truth)
    kinds = {d["kind"] for o in truth["orders"].values() for d in o["deviations"]}
    assert kinds == set(KINDS)


def test_pallets_only_on_bay_stays():
    events, _ = run()
    for e in events:
        if e.activity == "bay_stay":
            assert e.pallet in range(1, 11)
            assert e.attrs["corroborated"] is True
            assert e.attrs["start"] < e.time
        else:
            assert e.pallet is None


def test_vocabulary_from_recipes():
    """Every mission and program name comes from a recipe evidence step."""
    names = {s.attrs.get("mission") or s.attrs.get("program")
             for r in RECIPES.values() for op in r.operations for s in op.evidence}
    events, _ = run(p=0.05)
    acts = {e.activity for e in events}
    assert acts <= {"mission_started", "mission_ended", "bay_stay", "check_passed", "check_failed",
                    "test_result", "operation_started", "operation_done", "signal_changed"}
    for e in events:
        if e.activity.startswith("mission_"):
            assert e.attrs["mission"] in names
        if e.activity == "signal_changed":
            assert e.resource == "mill_cell" and e.attrs["signal"] == "program_running"
            assert e.attrs["program"] in names and e.attrs["old"] != e.attrs["new"]


def test_cell_events_inside_one_stay():
    """Without deviations, a cell event lies inside exactly one stay at its bay (the rule of Task 3)."""
    events, _ = run(orders=40)
    stays = [e for e in events if e.activity == "bay_stay"]
    for e in events:
        if e.resource in CELL_BAY:
            inside = [s for s in stays if s.attrs["bay"] == CELL_BAY[e.resource]
                      and s.attrs["start"] <= e.time <= s.time]
            assert len(inside) == 1, e


def test_bays_exclusive():
    events, _ = run(orders=40, p=0.05)
    by_bay = {}
    for e in events:
        if e.activity == "bay_stay":
            by_bay.setdefault(e.attrs["bay"], []).append((e.attrs["start"], e.time))
    for bay, spans in by_bay.items():
        spans.sort()
        for (s1, e1), (s2, e2) in zip(spans, spans[1:]):
            assert s2 >= e1, (bay, (s1, e1), (s2, e2))


@pytest.mark.parametrize("seed", [5, 6])
def test_fail_branch_present(seed):
    _, truth = run(seed=seed, orders=40, fail_p=0.5)
    gadgets = [o for o in truth["orders"].values() if o["recipe"] == "gadget"]
    names = [[op["name"] for op in o["operations"]] for o in gadgets]
    assert any("bin_covers" in n and "reload_covers" in n for n in names)
    assert all(n.count("check_covers") <= 3 for n in names)
