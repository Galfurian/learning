from collections import Counter

from pmlab.checks import run_checks
from pmlab.log import Entry, Trace
from pmlab.petri import Net
from pmlab.reference import pm4py, to_pm4py, to_pm4py_log


def trace(acts, case="c1"):
    return Trace(case, [Entry(case, a, "complete", float(i), "r", (case,), (f"e{i + 1}",), "inferred")
                        for i, a in enumerate(acts)])


# source -> a -> p1 -> b -> p2 -> c -> sink, and a fail loop: after b, x can put the token back before b.
NET = Net({"source", "p1", "p2", "sink"}, {"a": "a", "b": "b", "c": "c", "x": "x"},
          {("source", "a"), ("a", "p1"), ("p1", "b"), ("b", "p2"), ("p2", "c"), ("c", "sink"),
           ("p2", "x"), ("x", "p1")},
          Counter({"source": 1}), Counter({"sink": 1}))


def moves(al):
    return [(m.kind, m.activity, m.source_ids) for m in al.moves]


def checks(exe, check):
    done, fit = check.calls(exe.align, NET, trace("abc"))
    if not done:
        return
    check.ok(fit.cost == 0 and [m.kind for m in fit.moves] == ["sync"] * 3, "a fitting trace: three sync moves",
             moves(fit))
    check.ok(fit.moves[1].source_ids == ("e2",), "a sync move keeps the event id", moves(fit))
    loop = exe.align(NET, trace("abxbc"))
    check.ok(loop.cost == 0, "the loop x is in the model: no deviation", moves(loop))
    skip = exe.align(NET, trace("ac"))
    check.ok(skip.cost == 1 and moves(skip) == [("sync", "a", ("e1",)), ("model", "b", ()), ("sync", "c", ("e2",))],
             "skip b: one model move, between the ids around it", moves(skip))
    extra = exe.align(NET, trace(["a", "b", "unmapped:mission", "c"]))
    check.ok(extra.cost == 1 and ("log", "unmapped:mission", ("e3",)) in moves(extra),
             "an extra entry: one log move, with its event id", moves(extra))
    swap = exe.align(NET, trace("acb"))
    check.ok(swap.cost == 2, "a swap costs two moves", moves(swap))
    check.ok(exe.align(NET, trace("ab"), complete=False).cost == 0, "a running case: the missing c is not a deviation")
    check.ok(exe.align(NET, trace("ab")).cost == 1, "the same trace as complete: c is a model move")

    pn = to_pm4py(NET)
    for acts in ("abc", "ac", "acb", "abbc", "abxbc", "c", "aabc"):
        mine = exe.align(NET, trace(acts))
        (ref,) = pm4py.conformance_diagnostics_alignments(to_pm4py_log([trace(acts)]), *pn)
        check.ok(mine.cost == ref["cost"] // 10000, f"{acts}: the same cost as pm4py", (mine.cost, ref["cost"]))


run_checks(checks, __file__.replace("check.py", "exe07.py"))
