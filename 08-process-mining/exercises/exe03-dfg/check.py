from pmlab.checks import run_checks
from pmlab.log import Entry, Trace
from pmlab.reference import pm4py, to_pm4py_log


def trace(case, acts, step=10.0):
    entries = []
    for i, a in enumerate(acts):
        entries.append(Entry(case, a, "start", i * step, "r", (case,), (f"e{i}",), "inferred"))
        entries.append(Entry(case, a, "complete", i * step + 5, "r", (case,), (f"e{i}",), "inferred"))
    return Trace(case, entries)


# The textbook log L1 (van der Aalst): abcd x3, acbd x2, aed x1.
TRACES = [trace(f"c{i}", s) for i, s in enumerate(["abcd"] * 3 + ["acbd"] * 2 + ["aed"])] + [Trace("empty", [])]


def checks(exe, check):
    done, d = check.calls(exe.dfg, TRACES)
    if not done:
        return
    check.ok(dict(d.edges) == {("a", "b"): 3, ("b", "c"): 3, ("c", "d"): 3, ("a", "c"): 2, ("c", "b"): 2,
                               ("b", "d"): 2, ("a", "e"): 1, ("e", "d"): 1},
             "edge counts of L1 (start entries are not activities)", dict(d.edges))
    check.ok(dict(d.starts) == {"a": 6} and dict(d.ends) == {"d": 6}, "six traces start with a and end with d",
             (dict(d.starts), dict(d.ends)))
    check.ok(d.times.get(("a", "b")) == [10.0, 10.0, 10.0], "one gap per pair, in seconds", d.times.get(("a", "b")))
    check.ok(all(len(v) == d.edges[k] for k, v in d.times.items()), "as many gaps as pairs")
    ref, starts, ends = pm4py.discover_dfg(to_pm4py_log(TRACES))
    check.ok(dict(d.edges) == dict(ref), "the same edges as pm4py.discover_dfg", dict(ref))
    check.ok((dict(d.starts), dict(d.ends)) == (dict(starts), dict(ends)), "the same starts and ends as pm4py")


run_checks(checks, __file__.replace("check.py", "exe03.py"))
