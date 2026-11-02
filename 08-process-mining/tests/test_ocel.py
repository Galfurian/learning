import json

import pm4py
from helpers import entries_of

from pmlab.log import Entry
from pmlab.ocel import flatten, flattening_errors, ocel, to_ocel_json


def _types(o, kind):
    return {i for i, t in o.objects.items() if t == kind}


def test_ref_objects():
    o = ocel(entries_of("ref-order"))
    assert len(_types(o, "order")) == 1
    assert len(_types(o, "pallet")) == 3
    assert {"robot_a", "robot_b"} <= _types(o, "resource")


def test_every_resource_is_an_object():
    o = ocel(entries_of("train"))
    assert all(e.resource in o.objects for e in o.events)


def test_pallet_flatten_errors():
    o = ocel(entries_of("train"))
    assert flattening_errors(o, "pallet")["convergence"] > 0
    assert flattening_errors(o, "order")["convergence"] == 0


def test_flatten_copies_event_into_both_pallets():
    es = [
        Entry("order:1", "a", "complete", 1.0, "r", ("order:1", "pallet:1", "pallet:2", "r"), ("e1",), "derived"),
        Entry("order:1", "b", "complete", 2.0, "r", ("order:1", "pallet:1", "r"), ("e2",), "derived"),
    ]
    o = ocel(es)
    by = {t.case_id: t.activities for t in flatten(o, "pallet")}
    assert by == {"pallet:1": ("a", "b"), "pallet:2": ("a",)}
    assert flattening_errors(o, "pallet") == {"convergence": 1, "divergence": 0}


def test_divergence_synthetic():
    # pallet:1 is used by two orders, each with the same activity
    es = [
        Entry("order:1", "a", "complete", 1.0, "r", ("order:1", "pallet:1", "r"), ("e1",), "derived"),
        Entry("order:2", "a", "complete", 2.0, "r", ("order:2", "pallet:1", "r"), ("e2",), "derived"),
        Entry("order:2", "a", "complete", 3.0, "r", ("order:2", "pallet:2", "r"), ("e3",), "derived"),
    ]
    o = ocel(es)
    assert flattening_errors(o, "pallet") == {"convergence": 0, "divergence": 1}
    assert flattening_errors(o, "order")["divergence"] == 1  # order:2 repeats a with pallets 1 and 2


def test_train_numbers_are_stable():
    o = ocel(entries_of("train"))
    assert flattening_errors(o, "pallet") == {"convergence": 526, "divergence": 125}
    assert flattening_errors(o, "order") == {"convergence": 0, "divergence": 19}
    # Order divergence is a correct result: the fail branch repeats the covers
    # check on a new pallet, so one order holds two instances of that activity
    # with different pallets.
    repeated = set()
    for t in flatten(o, "order"):
        by_act = {}
        for e in t.entries:
            if e.lifecycle == "complete":
                by_act.setdefault(e.activity, []).append(frozenset(x for x in e.objects if o.objects[x] == "pallet"))
        repeated |= {a for a, ps in by_act.items() if len(ps) >= 2 and len(set(ps)) >= 2}
    assert repeated == {"check_covers", "reload_covers"}


def test_pm4py_reads(tmp_path):
    o = ocel(entries_of("train"))
    path = tmp_path / "log.jsonocel"
    path.write_text(json.dumps(to_ocel_json(o)), encoding="utf-8")
    got = pm4py.read_ocel2_json(str(path))
    assert len(got.events) == len(o.events)
    assert len(got.objects) == len(o.objects)
