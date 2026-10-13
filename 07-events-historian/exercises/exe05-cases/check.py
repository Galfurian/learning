from evlab.checks import run_checks
from evlab.records import Event


def ev(i, t, activity, resource="conveyor", pallet=None, case=None, kind="observed", **attrs):
    return Event(f"e{i}", activity, resource, t, t - 0.1, t + 0.1, (f"c{i}",), "r", "1", kind,
                 pallet, case, attrs)


EVENTS = [
    ev(1, 1, "destination_assigned", pallet=7, stop="bay5"),
    ev(2, 5, "destination_assigned", pallet=7, stop="bay4_1"),
    ev(3, 6, "check_failed", "qc_station", kind="derived"),
    ev(4, 7, "mission_started", "robot_b", kind="observed", mission="go_to_qc_bay"),
    ev(5, 8, "mission_ended", "robot_b", kind="observed", mission="go_to_qc_bay"),
    ev(6, 9, "mission_started", "robot_b", kind="observed", mission="go_home"),
    ev(7, 10, "mission_ended", "robot_b", kind="observed", mission="go_home"),
    ev(8, 20, "destination_assigned", pallet=8, stop="bay5"),
    ev(9, 21, "destination_assigned", pallet=8, stop="bay4_1"),
    ev(10, 21, "destination_assigned", pallet=9, stop="bay5"),
    ev(11, 22, "destination_assigned", pallet=9, stop="bay4_2"),
    ev(12, 23, "check_result_unknown", "qc_station", kind="derived"),
]


def checks(exe, check):
    done, out = check.calls(exe.assign_cases, EVENTS)
    if not done:
        return
    by_id = {event.event_id: event for event in out}
    check.ok(by_id["e1"].case_id == "p7#1", "bay5 starts p7#1", by_id["e1"].case_id)
    check.ok(by_id["e3"].case_id == "p7#1" and by_id["e3"].claim_kind == "inferred",
             "a QC result gets one inferred pallet link", (by_id["e3"].case_id, by_id["e3"].claim_kind))
    check.ok(by_id["e4"].case_id == "p7#1" and by_id["e6"].case_id == "p7#1",
             "an episode inherits the first safe correlation")
    check.ok(by_id["e12"].case_id is None and by_id["e12"].claim_kind == "derived",
             "an uncorrelated result stays case-less")
    check.ok(by_id["e12"].pallet is None, "an ambiguous join does not choose a pallet", by_id["e12"].pallet)


run_checks(checks, __file__.replace("check.py", "exe05.py"))
