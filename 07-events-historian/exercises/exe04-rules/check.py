from evlab.checks import run_checks
from evlab.records import Change


def ch(i, signal, old, new):
    return Change(f"c{i}", "ice-sim", "f", "v", signal.split(".")[0], signal, old, new, float(i), i - 0.2, i + 0.2,
                  None, "2026-10-13T10:00:00Z", "trace-position", 0, i)


def checks(exe, check):
    cs = [ch(1, "robot_b.mission", "", "go_to_bin"), ch(2, "robot_b.mission", "go_to_bin", "drop_covers_in_bin"),
          ch(3, "robot_b.busy", False, True), ch(4, "conveyor.destination.bay4_2", 0, 7),
          ch(5, "conveyor.destination.bay4_2", 7, 0), ch(6, "robot_b.mission", "drop_covers_in_bin", "")]
    done, out = check.calls(exe.derive_missions, cs)
    if not done:
        return
    got = [(e.activity, e.attrs.get("mission") or e.attrs.get("stop"), e.pallet) for e in out]
    check.ok(got == [("mission_started", "go_to_bin", None), ("mission_ended", "go_to_bin", None),
                     ("mission_started", "drop_covers_in_bin", None), ("destination_assigned", "bay4_2", 7),
                     ("destination_cleared", "bay4_2", 7), ("mission_ended", "drop_covers_in_bin", None)],
             "missions and destinations, end before start", got)
    check.ok([e.event_id for e in out] == [f"e{i}" for i in range(1, 7)], "ids e1, e2, ... in order")
    check.ok(all(e.claim_kind == "observed" and len(e.evidence) == 1 for e in out), "observed, one change each")
    check.ok(out[0].evidence == ("c1",) and out[0].event_time_lo == 0.8, "evidence and bounds from the change")


run_checks(checks, __file__.replace("check.py", "exe04.py"))
