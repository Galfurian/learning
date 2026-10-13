from evlab.collector import Notification, place, plain, to_changes
from evlab.mapping import EXAMPLE_MAPPING, load_mapping


def test_place_between_polls():
    polls = [(100.0, 0.0), (101.0, 5.0), (102.0, 10.0)]
    assert place(100.5, polls) == (2.5, 0.0, 5.0)
    assert place(99.0, polls) == (0.0, 0.0, 0.0)
    assert place(103.0, polls) == (10.0, 10.0, 10.0)


def test_to_changes_maps_values_and_keeps_arrival_order():
    mapping, _ = load_mapping(EXAMPLE_MAPPING)
    notes = [Notification(100.2, "robot_a", "robot_a.mission", "EX_go_home", None, 0),
             Notification(100.1, "robot_a", "robot_a.busy", True, None, 1),
             Notification(100.7, "robot_a", "robot_a.mission", "a real secret", None, 2)]
    changes = to_changes(notes, [(100.0, 0.0), (101.0, 1.0)], mapping, "t", "v")
    assert [c.change_id for c in changes] == ["c1", "c2", "c3"]
    assert [c.arrival_seq for c in changes] == [0, 1, 2]
    assert changes[0].new == "go_home" and changes[0].old is None
    assert changes[2].old == "go_home" and changes[2].new.startswith("unmapped:")
    assert changes[1].event_time_lo == 0.0 and changes[1].event_time_hi == 1.0
    assert changes[0].record_time.endswith("Z")


def test_plain_values():
    assert plain([1, 2]) == "[1, 2]" and plain(3) == 3 and plain(None) is None


def test_alarm_lists_become_logical_codes():
    class Msg:
        def __init__(self, n): self.number = n
    mapping, _ = load_mapping(EXAMPLE_MAPPING)
    assert plain([Msg(7054), Msg(1)]) == [7054, 1]
    out = mapping.logical_value("mill_cell.alarm_message", [7054, 1])
    assert out[1].startswith("unmapped:")


def test_text_values_that_are_numbers_or_message_lists():
    assert plain("0") == 0 and plain(" 12 ") == 12 and plain("go") == "go"
    assert plain("[Msg(kind=6, number=7054, text='x'), Msg(kind=6, number=7040, text='y')]") == [7054, 7040]
    assert plain("[]") == []
