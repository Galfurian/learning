from evlab.records import Change
from evlab.rules import clean, derive

_n = [0]


def ch(t, signal, old, new, cycle=0):
    _n[0] += 1
    machine = signal.split(".")[0]
    return Change(f"c{_n[0]}", "ice-sim", "fixture", "v", machine, signal, old, new, t, t - 0.1, t + 0.1, None,
                  "2026-10-13T10:00:00Z", "trace-position", cycle, _n[0])


def test_clean_drops_initial_and_unchanged_and_restarts_on_replay_cycle():
    cs = [ch(0, "robot_a.busy", None, False), ch(1, "robot_a.busy", False, True), ch(1.05, "robot_a.busy", True, True),
          ch(2, "robot_a.busy", True, False), ch(0, "robot_a.busy", None, False, cycle=1)]
    kept, report = clean(cs)
    assert [c.new for c in kept] == [True, False]
    assert report.dropped["initial value"] == 2 and report.dropped["unchanged or duplicate"] == 1


def test_missions_and_destinations_are_observed():
    events = derive([ch(1, "robot_b.mission", "", "go_to_bin"), ch(5, "robot_b.mission", "go_to_bin", ""),
                     ch(6, "conveyor.destination.bay4_2", 0, 7), ch(9, "conveyor.destination.bay4_2", 7, 0)])
    assert [(e.activity, e.claim_kind) for e in events] == [
        ("mission_started", "observed"), ("mission_ended", "observed"),
        ("destination_assigned", "observed"), ("destination_cleared", "observed")]
    assert events[2].pallet == 7 and events[2].attrs["stop"] == "bay4_2"


def test_qc_check_failed_is_derived_from_the_window():
    events = derive([ch(10, "qc_station.mission", "", "check_object"), ch(11.4, "qc_station.faults_total", 759, 760),
                     ch(11.5, "qc_station.mission", "check_object", "")])
    failed = [e for e in events if e.activity == "check_failed"]
    assert len(failed) == 1 and failed[0].claim_kind == "derived" and failed[0].pallet is None
    assert len(failed[0].evidence) == 3


def test_qc_check_with_no_result_signal_is_unknown():
    events = derive([ch(10, "qc_station.mission", "", "check_object"), ch(11, "qc_station.mission", "check_object", "")])
    assert "check_result_unknown" in [e.activity for e in events]


def test_fifo_slot_rewrite_is_not_a_movement():
    events = derive([ch(1, "conveyor.segment3.item0", 0, 7), ch(5, "conveyor.segment3.item0", 7, 0),
                     ch(5.1, "conveyor.segment3.item1", 0, 7)])
    assert [e.activity for e in events] == ["pallet_entered_segment"]


def test_alarm_codes():
    events = derive([ch(1, "mill_cell.alarm_message", [], ["vice_open"]), ch(2, "mill_cell.alarm_message", ["vice_open"], [])])
    assert [(e.activity, e.attrs["code"]) for e in events] == [("alarm_raised", "vice_open"), ("alarm_cleared", "vice_open")]


def test_change_without_event_time_never_reaches_the_rules():
    no_time = Change("c900", "line", None, None, "robot_a", "robot_a.mission", "", "go_home", None, None, None,
                     None, "2026-10-13T10:00:00Z", "unvalidated", 0, 900)
    kept, report = clean([ch(1, "robot_a.mission", None, ""), no_time])
    assert kept == [] and report.dropped["no event time"] == 1
    assert derive(kept) == []
