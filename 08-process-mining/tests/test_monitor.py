import time

from helpers import entries_of, truth_of, truth_order

from pmlab.compile import compile_recipe
from pmlab.log import Entry, Trace, to_log
from pmlab.monitor import candidates, prefix_at, status
from pmlab.performance import performance
from pmlab.recipes import load_recipes


def _nets():
    return {name: compile_recipe(r) for name, r in load_recipes().items()}


def _trace(name):
    (trace,) = to_log(entries_of(name))
    return trace


def test_shared_prefix_undecided():
    c = candidates(_trace("ref-prefix"), _nets())
    assert c.recipes == ["gadget", "parts_test"]
    assert c.claim_kind == "inferred"
    assert c.deciding == {"check_covers": ["gadget"], "mill_part": ["parts_test"]}
    assert c.deciding_ids == ()


def test_decided_after_divergence():
    trace = _trace("ref-order")
    c = candidates(prefix_at(trace, 400), _nets())
    assert c.recipes == ["gadget"]
    assert c.claim_kind == "derived"
    assert c.deciding == {}
    first_check = next(e for e in trace.entries if e.activity == "check_covers")
    assert c.deciding_ids == first_check.source_ids


def test_decided_status():
    trace = _trace("ref-order")
    stats = performance(to_log(entries_of("train")))
    s = status(trace, 400, _nets(), load_recipes(), stats)
    assert s.order == trace.case_id and s.now == 400
    assert s.candidates.recipes == ["gadget"]
    assert {o.activity for o in s.open} == {"check_covers", "buffer_board"}
    assert s.next == []          # both enabled operations are running already
    left = ("check_covers", "buffer_board", "assemble_gadget", "engrave_gadget", "deliver_gadget")
    assert s.remaining_s == sum(stats[a].p50 for a in left)


def test_empty_order():
    empty = Trace("order:99", [])
    c = candidates(empty, _nets())
    assert c.recipes == ["brick_demo", "gadget", "parts_test"]
    assert c.claim_kind == "inferred" and c.deciding_ids == ()
    s = status(empty, 0, _nets(), load_recipes(), {})
    assert s.next == ["reserve_pallet"]
    assert s.remaining_s is None and s.open == []


def test_undecided_status():
    s = status(_trace("ref-prefix"), 300, _nets(), load_recipes(), {})
    assert s.candidates.recipes == ["gadget", "parts_test"]
    assert s.next == ["test_board"]
    assert s.remaining_s is None


def test_no_recipe_fits():
    done = [("reserve_pallet", 10), ("load_bricks", 100), ("mill_part", 300)]
    entries = [Entry("order:98", a, "complete", t, "robot_a", ("order:98",), (f"e{i}",), "inferred")
               for i, (a, t) in enumerate(done, 1)]
    c = candidates(Trace("order:98", entries), _nets())
    assert c.recipes == [] and c.claim_kind == "derived"
    assert c.deciding == {} and c.deciding_ids == ()


def test_unmapped_ignored():
    trace = _trace("ref-prefix")
    extra = Entry(trace.case_id, "unmapped:mission", "complete", 230, "robot_b",
                  (trace.case_id,), ("e999999",), "observed")
    noisy = Trace(trace.case_id, sorted([*trace.entries, extra], key=lambda e: e.time))
    assert candidates(noisy, _nets()).recipes == ["gadget", "parts_test"]


def test_monitor_accuracy():
    nets = _nets()
    truth = truth_of("holdout")
    owner = {e: order for order, body in truth.items() for e in body["event_ids"]}
    checked = 0
    for trace in to_log(entries_of("holdout")):
        order = truth[truth_order(trace, owner)]
        if order["deviations"] or len(trace.entries) < 4:
            continue
        now = trace.entries[3].time
        assert order["recipe"] in candidates(prefix_at(trace, now), nets).recipes, trace.case_id
        checked += 1
    assert checked >= 20


def test_open_before_predecessor():
    # load_board starts (t=41) before reserve_pallet (t=209): an open start is
    # not a firing, so the recipes stay.
    c = candidates(prefix_at(_trace("ref-order"), 100), _nets())
    assert c.recipes == ["gadget", "parts_test"] and c.claim_kind == "inferred"


def test_sweep_never_empty():
    trace, nets = _trace("ref-order"), _nets()
    for now in range(0, 1119, 50):
        assert candidates(prefix_at(trace, now), nets).recipes, now


def test_many_open_operations_fast():
    ops = [op.name for op in load_recipes()["gadget"].operations][:10]
    entries = [Entry("order:97", a, "start", float(i), "robot_a", ("order:97",), (f"e{i}",), "inferred")
               for i, a in enumerate(ops, 1)]
    trace = Trace("order:97", entries)
    t0 = time.perf_counter()
    c = candidates(trace, _nets())
    s = status(trace, 100, _nets(), load_recipes(), {})
    assert time.perf_counter() - t0 < 2
    assert len(ops) == 10 and c.recipes == ["gadget"] and len(s.open) == 10
