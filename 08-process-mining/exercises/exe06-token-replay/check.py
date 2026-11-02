from collections import Counter

from pmlab.checks import run_checks
from pmlab.log import Entry, Trace
from pmlab.petri import Net
from pmlab.reference import pm4py, to_pm4py, to_pm4py_log


def trace(acts, case="c1"):
    return Trace(case, [Entry(case, a, "complete", float(i), "r", (case,), (f"e{i + 1}",), "inferred")
                        for i, a in enumerate(acts)])


# source -> a -> p1 -> b -> p2 -> c -> sink
SEQ = Net({"source", "p1", "p2", "sink"}, {"a": "a", "b": "b", "c": "c"},
          {("source", "a"), ("a", "p1"), ("p1", "b"), ("b", "p2"), ("p2", "c"), ("c", "sink")},
          Counter({"source": 1}), Counter({"sink": 1}))
# The same, with a silent transition that can skip b.
OPT = Net(set(SEQ.places), {**SEQ.transitions, "skip_b": None}, SEQ.arcs | {("p1", "skip_b"), ("skip_b", "p2")},
          Counter({"source": 1}), Counter({"sink": 1}))
# An AND-split after a and an AND-join at c; a silent transition fills one input place of c.
#   source -> a -> p1 -> skip_b (silent) -> p2 -> c -> sink
#                a -> q1 -> d -> q2 ---------> c
JOIN = Net({"source", "p1", "p2", "q1", "q2", "sink"}, {"a": "a", "skip_b": None, "d": "d", "c": "c"},
           {("source", "a"), ("a", "p1"), ("a", "q1"), ("p1", "skip_b"), ("skip_b", "p2"), ("q1", "d"),
            ("d", "q2"), ("p2", "c"), ("q2", "c"), ("c", "sink")},
           Counter({"source": 1}), Counter({"sink": 1}))


def checks(exe, check):
    done, fit = check.calls(exe.token_replay, SEQ, trace("abc"))
    if not done:
        return
    check.ok(fit.fitness == 1.0 and not fit.missing and not fit.remaining, "a fitting trace: fitness 1.0",
             (fit.fitness, fit.missing, fit.remaining))
    skip = exe.token_replay(SEQ, trace("ac"))
    check.ok(skip.missing == Counter({"p2": 1}) and skip.remaining == Counter({"p1": 1}),
             "skip b: one missing token in p2, one remaining in p1", (skip.missing, skip.remaining))
    check.ok(abs(skip.fitness - 2 / 3) < 1e-9, "skip b: fitness 0.5*(1-1/3) + 0.5*(1-1/3)", skip.fitness)
    check.ok([a for a, _ in skip.problems] == ["c"] and skip.problems[0][1] == ("e2",),
             "the problem is at c, with its event id", skip.problems)
    check.ok(exe.token_replay(OPT, trace("ac")).fitness == 1.0, "a silent transition enables c: no missing token")
    noisy = exe.token_replay(SEQ, trace(["a", "unmapped:mission", "b", "c"]))
    check.ok(noisy.fitness == 1.0, "an activity with no transition is skipped, as pm4py does", noisy.fitness)
    running = exe.token_replay(SEQ, trace("ab"), complete=False)
    ended = exe.token_replay(SEQ, trace("ab"))
    check.ok(running.fitness == 1.0 and ended.fitness < 1.0,
             "a running case (complete=False) is not a deviation; the same trace as complete is",
             (running.fitness, ended.fitness))

    join = exe.token_replay(JOIN, trace("ac"))
    check.ok(join.missing == Counter({"q2": 1}) and (join.consumed, join.produced) == (5, 5),
             "skip d: the silent transition fills p2 (its tokens count), only q2 is missing",
             (join.missing, join.consumed, join.produced))

    for name, net, acts in (("SEQ", SEQ, "abc"), ("SEQ", SEQ, "ac"), ("SEQ", SEQ, "acb"), ("SEQ", SEQ, "abbc"),
                            ("OPT", OPT, "ac"), ("OPT", OPT, "acc"), ("JOIN", JOIN, "adc"), ("JOIN", JOIN, "ac"),
                            ("JOIN", JOIN, "acd")):
        mine = exe.token_replay(net, trace(acts))
        (ref,) = pm4py.conformance_diagnostics_token_based_replay(to_pm4py_log([trace(acts)]), *to_pm4py(net))
        check.ok(abs(mine.fitness - ref["trace_fitness"]) < 1e-9
                 and (sum(mine.missing.values()), sum(mine.remaining.values()))
                 == (ref["missing_tokens"], ref["remaining_tokens"]),
                 f"{name} {acts}: the same fitness, missing and remaining as pm4py",
                 (mine.fitness, ref["trace_fitness"], ref["missing_tokens"], ref["remaining_tokens"]))


run_checks(checks, __file__.replace("check.py", "exe06.py"))
