import pm4py
from helpers import entries_of, to_pm4py_log, truth_of, truth_order

from pmlab.align import align
from pmlab.compile import compile_recipe
from pmlab.log import Entry, Trace, to_log
from pmlab.petri import Net
from pmlab.recipes import load_recipes
from pmlab.reference import to_pm4py

MAIN = ("reserve_pallet", "load_board", "test_board", "buffer_board", "load_covers",
        "check_covers", "assemble_gadget", "engrave_gadget", "deliver_gadget")


def _gadget() -> Net:
    return compile_recipe(load_recipes()["gadget"])


def test_fit_trace_costs_zero():
    fit = [t for t in to_log(entries_of("train")) if t.activities == MAIN]
    result = align(_gadget(), fit[0])
    assert result.cost == 0
    assert [m.kind for m in result.moves] == ["sync"] * len(MAIN)
    assert all(m.source_ids for m in result.moves)


def test_skip_is_model_move():
    # The order is still running (no engrave, no deliver): align it as a prefix,
    # so the only deviation is the check that did not run again after the reload.
    (trace,) = to_log(entries_of("ref-skip-check"))
    result = align(_gadget(), trace, complete=False)
    model = [m for m in result.moves if m.kind == "model"]
    assert [(m.activity, m.source_ids) for m in model] == [("check_covers", ())]
    assert not [m for m in result.moves if m.kind == "log"]
    assert result.cost == 1
    # As a complete trace the missing tail adds model moves, but check_covers is still skipped once.
    full = align(_gadget(), trace)
    assert [m.activity for m in full.moves if m.kind == "model"].count("check_covers") == 1


def test_extra_is_log_move():
    fit = [t for t in to_log(entries_of("train")) if t.activities == MAIN][0]
    done = [e for e in fit.entries if e.lifecycle == "complete"]
    extra = Entry(fit.case_id, "unmapped:mission", "complete", done[2].time, "robot_a",
                  (f"{fit.case_id}",), ("e999998", "e999999"), "observed")
    i = fit.entries.index(done[2]) + 1
    noisy = Trace(fit.case_id, [*fit.entries[:i], extra, *fit.entries[i:]])
    result = align(_gadget(), noisy)
    logs = [m for m in result.moves if m.kind == "log"]
    assert [(m.activity, m.source_ids) for m in logs] == [("unmapped:mission", ("e999998", "e999999"))]
    assert result.cost == 1
    assert [m.kind for m in result.moves].count("sync") == len(MAIN)


def test_prefix_alignment():
    (trace,) = to_log(entries_of("ref-prefix"))
    net = _gadget()
    assert align(net, trace, complete=False).cost == 0
    assert align(net, trace).cost > 0


def _deviating_traces() -> list[tuple[Trace, str]]:
    """Traces whose truth order has deviations, with their truth recipe: all of
    train (sorted by case id), then holdout if train has fewer than 15; at most 30."""
    out = []
    for name in ("train", "holdout"):
        if name == "holdout" and len(out) >= 15:
            break
        truth = truth_of(name)
        owner = {e: order for order, body in truth.items() for e in body["event_ids"]}
        for trace in sorted(to_log(entries_of(name)), key=lambda t: t.case_id):
            order = truth_order(trace, owner)
            if truth[order]["deviations"]:
                out.append((trace, truth[order]["recipe"]))
    return out[:30]


def test_cost_matches_pm4py():
    nets = {name: compile_recipe(r) for name, r in load_recipes().items()}
    pm = {name: to_pm4py(n) for name, n in nets.items()}
    cases = _deviating_traces()
    assert len(cases) >= 15
    costs = []
    for trace, recipe in cases:
        ours = align(nets[recipe], trace)
        (ref,) = pm4py.conformance_diagnostics_alignments(to_pm4py_log([trace]), *pm[recipe])
        assert ours.cost == ref["cost"] // 10000, (trace.case_id, recipe)
        assert ours.cost == sum(m.kind != "sync" for m in ours.moves)
        costs.append(ours.cost)
    assert sum(c > 0 for c in costs) >= len(costs) // 2
