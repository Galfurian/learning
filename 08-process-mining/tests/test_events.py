from pmlab.events import Event, read_events, write_events


def test_event_roundtrip(tmp_path):
    header = {"log": "demo", "injected": [{"kind": "skip", "event_id": "e2"}]}
    events = [
        Event("e1", "mission_started", "robot_a", 1.5, None, "observed", {"mission": "go_home"}, ("n1",)),
        Event("e2", "bay_stay", "conveyor", 3.0, 7, "derived", {"bay": "load"}, ("e1", "n2")),
    ]
    path = tmp_path / "sub" / "log.jsonl"
    write_events(path, header, events)
    got_header, got_events = read_events(path)
    assert got_header == header
    assert got_events == events
