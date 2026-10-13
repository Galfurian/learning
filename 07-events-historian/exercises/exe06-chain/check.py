from evlab.checks import run_checks
from evlab.records import Event


def ev(i, t, activity, resource="conveyor", pallet=7, kind="observed", **attrs):
    return Event(f"e{i}", activity, resource, t, t - 0.1, t + 0.1, (f"c{i}",), "r", "1", kind,
                 pallet, "p7#1", attrs)


EVENTS = [
    ev(1, 10, "pallet_entered_segment", segment="segment3"),
    ev(2, 20, "pallet_left_segment", segment="segment3"),
    ev(3, 22, "destination_assigned", stop="bay4_1"),
    ev(4, 30, "check_failed", resource="qc_station", kind="inferred"),
    ev(5, 50, "destination_cleared", stop="bay4_1"),
    ev(6, 60, "pallet_entered_segment", segment="segment6"),
]


def checks(exe, check):
    done, out = check.calls(exe.chain, EVENTS, "p7#1")
    if not done:
        return
    check.ok([event.event_id for event in out.steps] == ["e3", "e4", "e5"],
             "destination events are visits and the QC event is a step", out.ids)
    check.ok(len(out.visits) == 1 and out.visits[0].corroborated,
             "a visit is corroborated by leaving the loop")
    check.ok(out.loop_events == 3 and "inferred" in out.coverage[0],
             "loop evidence and coverage are retained", (out.loop_events, out.coverage))
    unknown = exe.chain(EVENTS, "p9#1")
    check.ok(unknown.steps == [] and unknown.coverage == ["no event of this case in the recording"],
             "an unknown case abstains", unknown.coverage)


run_checks(checks, __file__.replace("check.py", "exe06.py"))
