import math

from helpers import entries_of

from pmlab.log import to_log
from pmlab.performance import open_operations, performance
from pmlab.recipes import load_recipes


def _stats():
    return performance(to_log(entries_of("train")))


def _trace(name):
    (trace,) = to_log(entries_of(name))
    return trace


def _recipe_of(trace):
    names = {e.activity for e in trace.entries}
    for recipe in load_recipes().values():
        if names <= {o.name for o in recipe.operations}:
            return recipe
    raise AssertionError("no recipe")


def test_engrave_baseline():
    s = _stats()["engrave_gadget"]
    assert math.isclose(s.p50, 150, rel_tol=0.15)
    assert s.count > 5 and s.p50 <= s.p95 <= s.max


def test_waiting_exists():
    assert any(s.wait_p95 > 30 for s in _stats().values())


def test_stuck_ref():
    stats = _stats()
    assert stats["engrave_gadget"].p95 > 200
    trace = _trace("ref-stuck")
    (op,) = [o for o in open_operations(trace, 1400, stats, _recipe_of(trace)) if o.activity == "engrave_gadget"]
    assert math.isclose(op.age, 482) and op.verdict == "unusual"
    assert op.nominal_s == 150 and op.source_ids

    trace = _trace("ref-order")
    (op,) = [o for o in open_operations(trace, 1118, stats, _recipe_of(trace)) if o.activity == "engrave_gadget"]
    assert math.isclose(op.age, 200) and op.verdict == "running"


def test_now_before_start():
    trace = _trace("ref-order")
    assert not [o for o in open_operations(trace, 900, _stats(), _recipe_of(trace)) if o.activity == "engrave_gadget"]
