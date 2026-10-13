from evlab.checks import run_checks
from evlab.records import Change


def ch(i, signal, new, cycle=0, seq=None):
    return Change(f"c{i}", "ice-sim", "f", "v", signal.split(".")[0], signal, None, new, float(i), float(i), float(i),
                  None, "2026-10-13T10:00:00Z", "trace-position", cycle, i if seq is None else seq)


def checks(exe, check):
    cs = [ch(1, "a.busy", False), ch(2, "a.busy", True), ch(3, "a.busy", True), ch(4, "b.n", 5),
          ch(5, "a.busy", False), ch(6, "a.busy", False, cycle=1), ch(7, "a.busy", True, cycle=1)]
    done, out = check.calls(exe.clean, cs)
    if not done:
        return
    kept, report = out
    ids = [c.change_id for c in kept]
    check.ok(ids == ["c2", "c5", "c7"], "initial values out, duplicates out, restart after a new replay cycle", ids)
    check.ok(report.dropped.get("initial value") == 3, "three initial values (a, b, a after the restart)",
             dict(report.dropped))
    check.ok(report.dropped.get("unchanged or duplicate") == 1, "one duplicate", dict(report.dropped))
    shuffled = [ch(2, "a.busy", True, seq=2), ch(1, "a.busy", False, seq=1)]
    kept, _ = exe.clean(shuffled)
    check.ok([c.change_id for c in kept] == ["c2"], "arrival order decides, not the list order")


run_checks(checks, __file__.replace("check.py", "exe03.py"))
