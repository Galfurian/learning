from evlab.cases import CASES_VERSION, CORRELATION_RULE, assign_cases
from evlab.records import Event
from evlab.rules import clean, derive

from test_fixture import build


def fixture_events():
    _, changes, _ = build()
    kept, _ = clean(changes)
    return derive(kept)


def test_cycles_are_started_at_bay5_and_reused_pallets_get_new_cases():
    events = assign_cases(fixture_events())
    bay5 = [event for event in events if event.activity == "destination_assigned" and event.attrs.get("stop") == "bay5"]
    assert [(event.pallet, event.case_id) for event in bay5] == [(7, "p7#1"), (8, "p8#1"), (7, "p7#2")]
    assert all(event.case_id is None for event in events if event.pallet == 9)
    assert all(event.case_id == "p7#2" for event in events if event.pallet == 7 and event.event_time >= 180)


def test_qc_and_rework_missions_are_inferred_from_the_bay4_assignment():
    events = assign_cases(fixture_events())
    failed = next(event for event in events if event.activity == "check_failed")
    passed = next(event for event in events if event.activity == "check_passed")
    rework = [
        event for event in events
        if event.resource == "robot_b" and event.attrs.get("mission") in {
            "take_cover_top_from_pallet", "take_cover_bottom_from_pallet", "go_to_bin", "drop_covers_in_bin"
        }
    ]
    assert failed.case_id == "p7#1" and failed.pallet == 7
    assert passed.case_id == "p8#1" and passed.pallet == 8
    assert rework and {event.case_id for event in rework} == {"p7#1"}
    assert all(event.claim_kind == "inferred" for event in [failed, passed, *rework])
    assert all(event.rule == CORRELATION_RULE and event.rule_version == CASES_VERSION for event in [failed, passed, *rework])
    episode = [event for event in events if event.resource == "robot_b" and event.attrs.get("mission") == "go_home"]
    assert episode and {event.case_id for event in episode} == {"p7#1"}
    assert all(
        any(word in event.confidence_note for word in ("occupancy", "episode", "fallback"))
        for event in [failed, passed, *rework, *episode]
    )


def test_missing_correlation_stays_derived_and_case_less():
    events = assign_cases(fixture_events())
    unknown = next(event for event in events if event.activity == "check_failed" and event.event_time == 301.0)
    assert unknown.case_id is None and unknown.pallet is None
    assert unknown.claim_kind == "derived"


def test_ambiguous_bay_assignments_abstain():
    marker_a = Event("e1", "destination_assigned", "conveyor", 8.0, 7.0, 9.0, ("c1",), "destinations", "1", "observed", 1, "p1#1", {"stop": "bay4_1"})
    marker_b = Event("e2", "destination_assigned", "conveyor", 10.0, 9.0, 11.0, ("c2",), "destinations", "1", "observed", 2, "p2#1", {"stop": "bay4_2"})
    check = Event("e3", "check_failed", "qc_station", 11.0, 10.0, 12.0, ("c3",), "qc_checks", "1", "derived")
    result = assign_cases([marker_a, marker_b, check])
    assert result[-1].case_id is None and result[-1].pallet is None and result[-1].claim_kind == "derived"


def test_non_correlated_mission_is_not_given_a_pallet():
    marker = Event("e1", "destination_assigned", "conveyor", 10.0, 9.0, 11.0, ("c1",), "destinations", "1", "observed", 1, "p1#1", {"stop": "bay4_1"})
    storage = Event("e2", "mission_started", "robot_b", 11.0, 10.0, 12.0, ("c2",), "missions", "1", "observed", attrs={"mission": "go_to_storage"})
    result = assign_cases([marker, storage])
    assert result[-1].case_id is None and result[-1].pallet is None and result[-1].claim_kind == "observed"


def test_assignment_window_is_the_fallback_after_occupancy_ends():
    marker = Event("e1", "destination_assigned", "conveyor", 10.0, 9.0, 11.0, ("c1",), "destinations", "1", "observed", 1, "p1#1", {"stop": "bay4_1"})
    cleared = Event("e2", "destination_cleared", "conveyor", 20.0, 19.0, 21.0, ("c2",), "destinations", "1", "observed", 1, "p1#1", {"stop": "bay4_1"})
    late = Event("e3", "mission_started", "robot_b", 50.0, 49.0, 51.0, ("c3",), "missions", "1", "observed", attrs={"mission": "go_to_bin"})
    result = assign_cases([marker, cleared, late])
    assert result[-1].case_id == "p1#1" and result[-1].pallet == 1
    assert "fallback" in result[-1].confidence_note
