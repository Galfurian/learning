import pytest

from evlab.mapping import EXAMPLE_MAPPING, Mapping, load_mapping
from evlab.records import Change, Event, Manifest, read_recording, write_recording


def change(i: int, new) -> Change:
    return Change(f"c{i}", "ice-sim", "t", "v1", "robot_a", "robot_a.mission", "", new, 10.0 + i, 9.5 + i, 10.5 + i,
                  None, "2026-10-13T10:00:00Z", "trace-position")


def test_recording_round_trip(tmp_path):
    m = Manifest("ice-sim", "t", "v1", "abc", "1", 1.0, "trace-position")
    write_recording(tmp_path / "r.jsonl", m, [change(1, "go_home"), change(2, "")])
    m2, changes = read_recording(tmp_path / "r.jsonl")
    assert m2 == m and m2.key() == m.key() and [c.new for c in changes] == ["go_home", ""]
    assert Manifest("ice-sim", "t", "v1", "abc", "1", 5.0, "trace-position").key() != m.key()


def test_event_rules():
    e = Event("e1", "mission_started", "robot_a", 1.0, 0.5, 1.5, ("c1", "c2"), "missions", "1", "derived")
    assert Event.from_json(e.to_json()) == e
    with pytest.raises(ValueError):
        Event("e2", "x", "robot_a", 1.0, 1.0, 1.0, (), "r", "1", "inferred")
    with pytest.raises(ValueError):
        Event("e3", "x", "robot_a", 1.0, 1.0, 1.0, ("c1",), "r", "1", "guessed")


def test_mapping_example_and_values():
    mapping, path = load_mapping(EXAMPLE_MAPPING)
    assert path == EXAMPLE_MAPPING and "robot_a" in mapping.machines()
    sig = mapping.signals["robot_a.mission"]
    assert mapping.signal_of("robot_a", sig.node_id) == sig
    assert mapping.logical_value("robot_a.mission", "EX_go_home") == "go_home"
    assert mapping.logical_value("robot_a.mission", "secret name").startswith("unmapped:")
    assert mapping.logical_value("robot_a.busy", True) is True
    assert mapping.logical_value("mill_cell.alarm_status", "Some real text").startswith("unmapped:")


def test_mapping_rejects_duplicates_and_unknown_value_maps():
    with pytest.raises(ValueError):
        Mapping({"machines": {"a": {"signals": {"x": "n1"}}}, "values": {"a.y": {}}})


def test_change_invariants():
    with pytest.raises(ValueError):
        Change("c9", "ice-sim", "t", "v1", "robot_a", "robot_a.busy", False, True, 5.0, 6.0, 4.0, None,
               "2026-10-13T10:00:00Z", "trace-position")
    with pytest.raises(ValueError):
        Change("c9", "ice-sim", "t", "v1", "robot_a", "robot_a.busy", False, True, 5.0, 5.0, 5.0, None,
               "2026-10-13 10:00", "trace-position")
    with pytest.raises(ValueError):
        Change("c9", "line", "t", None, "robot_a", "robot_a.busy", False, True, None, None, None, "x",
               "2026-10-13T10:00:00Z", "ntp")
    with pytest.raises(TypeError):
        Change("c9", "ice-sim", "t", "v1", "robot_a", "robot_a.busy", False, object(), 5.0, 5.0, 5.0, None,
               "2026-10-13T10:00:00Z", "trace-position")
