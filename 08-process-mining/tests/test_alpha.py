from collections import Counter

import pm4py
from helpers import entries_of
from pm4py.algo.conformance.tokenreplay import algorithm as token_replay

from pmlab.alpha import alpha, footprint
from pmlab.log import Entry, Trace, to_log
from pmlab.recipes import load_recipes
from pmlab.reference import to_pm4py, to_pm4py_log


def _trace(case: str, acts: str) -> Trace:
    return Trace(case, [Entry(case, a, "complete", float(i), "r", (), (f"e{i}",), "observed") for i, a in enumerate(acts)])


def _l1() -> list[Trace]:
    seqs = ["abcd"] * 3 + ["acbd"] * 2 + ["aed"]
    return [_trace(f"c{i}", s) for i, s in enumerate(seqs)]


def _labels(net) -> set[tuple[frozenset[str], frozenset[str]]]:
    out = set()
    for p in net.places:
        ins = frozenset(net.transitions[t] for t, q in net.arcs if q == p and t in net.transitions)
        outs = frozenset(net.transitions[t] for q, t in net.arcs if q == p and t in net.transitions)
        out.add((ins, outs))
    return out


def test_footprint():
    fp = footprint(_l1())
    assert fp[("a", "b")] == "->" and fp[("b", "a")] == "<-"
    assert fp[("b", "c")] == "||" and fp[("a", "c")] == "->"
    assert fp[("b", "e")] == "#" and fp[("a", "a")] == "#"


def test_alpha_textbook():
    net = alpha(_l1())
    f = frozenset
    assert _labels(net) == {
        (f(), f("a")),
        (f("d"), f()),
        (f("a"), f("be")),
        (f("a"), f("ce")),
        (f("be"), f("d")),
        (f("ce"), f("d")),
    }
    assert len(net.places) == 6 and net.initial == Counter({"i": 1}) and net.final == Counter({"o": 1})
    assert sorted(net.transitions.values()) == list("abcde")


def test_alpha_matches_pm4py():
    # Recipe identity is not in the log (order ids are not recipe names), so
    # select the main-branch traces of brick_demo by their activity set.
    names = {op.name for op in load_recipes()["brick_demo"].operations}
    traces = [t for t in to_log(entries_of("train")) if t.activities and set(t.activities) <= names]
    assert traces
    mine = alpha(traces)
    net, im, fm = pm4py.discover_petri_net_alpha(to_pm4py_log(traces))
    ref = set()
    for p in net.places:
        ins = frozenset(a.source.label for a in p.in_arcs)
        outs = frozenset(a.target.label for a in p.out_arcs)
        ref.add((ins, outs))
    assert _labels(mine) == ref


def test_alpha_short_loop_fails():
    # gadget traces with the fail branch: check_covers appears twice (a loop
    # of length 2 through bin_covers); Alpha cannot replay it.
    traces = [t for t in to_log(entries_of("train")) if "bin_covers" in t.activities]
    assert traces
    net, im, fm = to_pm4py(alpha(traces))
    res = token_replay.apply(to_pm4py_log(traces), net, im, fm)
    fitness = sum(r["trace_fitness"] for r in res) / len(res)
    assert fitness < 1.0


def test_alpha_self_loop_matches_pm4py():
    # A self-loop activity (a#a does not hold) is in no place.
    traces = [_trace("c0", "abd"), _trace("c1", "aabd")]
    net, _, _ = pm4py.discover_petri_net_alpha(to_pm4py_log(traces))
    ref = {(frozenset(x.source.label for x in p.in_arcs), frozenset(x.target.label for x in p.out_arcs)) for p in net.places}
    assert _labels(alpha(traces)) == ref
