import pytest

from evlab.historian import Historian, StaleCacheError, cache_path
from evlab.records import Change, Event, Manifest


def make_manifest(speed=1.0):
    return Manifest("ice-sim", "fixture", "v1", "mapping", "collector-1", speed, "trace-position")


def make_change(number, *, time=10.0, signal="robot_a.mission", new="go_home", arrival=None):
    return Change(
        f"c{number}", "ice-sim", "fixture", "v1", "robot_a", signal, "", new,
        time, time - 0.1, time + 0.1, None, "2026-10-13T10:00:00Z",
        "trace-position", 0, number if arrival is None else arrival,
    )


def test_load_is_idempotent_and_queries_are_typed():
    manifest = make_manifest()
    changes = [make_change(1, time=10.0), make_change(2, time=20.0, signal="robot_a.busy", new=True)]
    with Historian.memory() as historian:
        key = historian.load(manifest, changes)
        assert historian.load(manifest, changes) == key
        assert len(historian.changes()) == 2
        result = historian.changes(machine="robot_a", path_like="robot_a.%", since=10, until=20)
        assert [c.change_id for c in result] == ["c1"]
        assert [c.change_id for c in historian.changes(until=10.0)] == []
        assert [c.change_id for c in historian.changes(since=20.0)] == ["c2"]
        with pytest.raises(ValueError):
            historian.changes(since=4, until=3)
        with pytest.raises(ValueError):
            historian.changes(limit=0)
        with pytest.raises(TypeError):
            historian.events(pallet=True)


def test_events_round_trip_and_evidence_are_idempotent():
    manifest = make_manifest()
    event = Event(
        "e1", "mission_started", "robot_a", 10.0, 9.9, 10.1,
        ("c2", "c1"), "mission-rule", "v1", "derived", 7, "p7#1",
        {"mission": "go_home"}, "from mission value",
    )
    with Historian.memory() as historian:
        key = historian.load(manifest, [make_change(1), make_change(2)])
        historian.add_events(manifest, [event])
        historian.add_events(key, [event])
        assert historian.events(case_id="p7#1")[0] == event
        assert historian.evidence(key, "e1") == ["c2", "c1"]
        with pytest.raises(ValueError):
            historian.add_events(key, [Event("e2", "x", "robot_a", 1, 1, 1, ("missing",), "r", "1", "derived")])


def test_cache_manifest_rejects_stale_recording(tmp_path):
    first = make_manifest()
    second = make_manifest(speed=5.0)
    path = cache_path(tmp_path, first)
    with Historian.open(path) as historian:
        historian.load(first, [make_change(1)])
    with pytest.raises(StaleCacheError):
        Historian.open(path, expected=second)


def test_cache_path_uses_manifest_key(tmp_path):
    manifest = make_manifest()
    assert cache_path(tmp_path, manifest).name.endswith(".sqlite3")
    assert cache_path(tmp_path, manifest) != tmp_path / f"{manifest.key()}.sqlite3"   # versions are in the key



def test_a_new_rules_version_is_a_new_cache(tmp_path, monkeypatch):
    from evlab import rules
    from evlab.historian import cache_key
    from evlab.records import Manifest
    manifest = Manifest("ice-sim", "t", "v", "m", "1", 1.0, "trace-position")
    before = cache_key(manifest)
    monkeypatch.setattr(rules, "RULES_VERSION", "999")
    assert cache_key(manifest) != before
