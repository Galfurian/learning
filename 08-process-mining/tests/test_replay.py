import pm4py
from helpers import entries_of, to_pm4py_log, truth_of, truth_order

from pmlab.compile import compile_recipe
from pmlab.log import Trace, to_log
from pmlab.petri import Net
from pmlab.recipes import load_recipes
from pmlab.reference import to_pm4py
from pmlab.replay import token_replay


def _gadget() -> Net:
    return compile_recipe(load_recipes()["gadget"])


def test_fit_trace():
    main = ("reserve_pallet", "load_board", "test_board", "buffer_board", "load_covers",
            "check_covers", "assemble_gadget", "engrave_gadget", "deliver_gadget")
    fit = [t for t in to_log(entries_of("train")) if t.activities == main]
    assert fit
    assert token_replay(_gadget(), fit[0]).fitness == 1.0


def test_skip_check():
    (trace,) = to_log(entries_of("ref-skip-check"))
    result = token_replay(_gadget(), trace)
    assert result.fitness < 1.0
    names = [a for a, _ in result.problems]
    assert "assemble_gadget" in names
    ids = dict(result.problems)["assemble_gadget"]
    assert ids and all(i.startswith("e") for i in ids)


def test_running_not_deviation():
    (trace,) = to_log(entries_of("ref-order"))
    net = _gadget()
    assert token_replay(net, trace, complete=False).fitness == 1.0
    assert token_replay(net, trace, complete=True).fitness < 1.0


def test_unknown_activity_is_ignored_as_in_pm4py():
    (trace,) = to_log(entries_of("ref-skip-check"))
    extra = trace.entries[0].__class__(**{**trace.entries[0].__dict__, "activity": "unmapped:zzz"})
    noisy = Trace(trace.case_id, [*trace.entries[:2], extra, *trace.entries[2:]])
    a, b = token_replay(_gadget(), trace), token_replay(_gadget(), noisy)
    assert (a.fitness, a.missing, a.remaining) == (b.fitness, b.missing, b.remaining)


def test_matches_pm4py():
    truth = truth_of("train")
    owner = {e: order for order, body in truth.items() for e in body["event_ids"]}
    recipes = load_recipes()
    nets = {name: compile_recipe(r) for name, r in recipes.items()}
    pm = {name: to_pm4py(n) for name, n in nets.items()}
    # Every train trace: the first 30 by id missed order:33, where a silent transition fills one input
    # place of an AND-join and pm4py counts its tokens.
    traces = to_log(entries_of("train"))
    assert len(traces) == 200
    for trace in traces:
        recipe = truth[truth_order(trace, owner)]["recipe"]
        ours = token_replay(nets[recipe], trace)
        (ref,) = pm4py.conformance_diagnostics_token_based_replay(to_pm4py_log([trace]), *pm[recipe])
        assert abs(ours.fitness - ref["trace_fitness"]) < 1e-9, (trace.case_id, recipe)
        assert (sum(ours.missing.values()), sum(ours.remaining.values())) == (
            ref["missing_tokens"], ref["remaining_tokens"]), (trace.case_id, recipe)
