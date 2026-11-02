from collections import Counter

from pmlab.checks import run_checks
from pmlab.log import Entry, Trace
from pmlab.reference import pm4py, to_pm4py, to_pm4py_log


def trace(case, acts):
    return Trace(case, [Entry(case, a, "complete", float(i), "r", (case,), (f"e{i}",), "inferred")
                        for i, a in enumerate(acts)])


L1 = [trace(f"c{i}", s) for i, s in enumerate(["abcd"] * 3 + ["acbd"] * 2 + ["aed"])]
# A short loop, as the fail branch of a recipe: check (c), bin (x), check again.
LOOP = [trace("c0", "abcd"), trace("c1", "abcxcd")]


def places(net):
    """Each place as (labels in, labels out): place names do not matter."""
    out = set()
    for p in net.places:
        ins = frozenset(net.transitions[t] for t, q in net.arcs if q == p and t in net.transitions)
        outs = frozenset(net.transitions[t] for q, t in net.arcs if q == p and t in net.transitions)
        out.add((ins, outs))
    return out


def pm4py_places(traces):
    net, _, _ = pm4py.discover_petri_net_alpha(to_pm4py_log(traces))
    return {(frozenset(a.source.label for a in p.in_arcs), frozenset(a.target.label for a in p.out_arcs))
            for p in net.places}


def checks(exe, check):
    done, net = check.calls(exe.alpha, L1)
    if not done:
        return
    f = frozenset
    check.ok(places(net) == {(f(), f("a")), (f("d"), f()), (f("a"), f("be")), (f("a"), f("ce")),
                             (f("be"), f("d")), (f("ce"), f("d"))},
             "the six places of L1 (textbook)", places(net))
    check.ok(sorted(net.transitions.values()) == list("abcde"), "one transition per activity",
             sorted(net.transitions.values()))
    check.ok(net.initial == Counter({"i": 1}) and net.final == Counter({"o": 1}), "one token in i, end in o")
    check.ok(places(net) == pm4py_places(L1), "the same places as pm4py.discover_petri_net_alpha")
    fit = pm4py.fitness_token_based_replay(to_pm4py_log(L1), *to_pm4py(net))
    check.ok(fit["log_fitness"] == 1.0, "L1 replays on your net with fitness 1.0", fit["log_fitness"])

    _, loop = check.calls(exe.alpha, LOOP)
    if loop is None:
        return
    check.ok(places(loop) == pm4py_places(LOOP), "a short loop: the same places as pm4py", places(loop))
    fit = pm4py.fitness_token_based_replay(to_pm4py_log(LOOP), *to_pm4py(loop))
    check.ok(fit["log_fitness"] < 1.0, "a short loop: the Alpha net cannot replay its own log (a known limit)",
             fit["log_fitness"])


run_checks(checks, __file__.replace("check.py", "exe04.py"))
