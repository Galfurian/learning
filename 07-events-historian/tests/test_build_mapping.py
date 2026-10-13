import pytest

from evlab.build_mapping import LOCAL_DIR, resolve, write_local

PATTERNS = {"machines": {"robot_a": {"server": "s1", "signals": {"mission": "Mission/Name", "busy": "Busy"}}},
            "values": {"robot_a.mission": {"realGo": "go_home"}}}
CATALOG = {"s1": [{"path": "Objects/X/Mission/Name", "node_id": "ns=2;i=1"},
                  {"path": "Objects/X/Busy", "node_id": "ns=2;i=2"}]}


def test_resolve():
    m = resolve(PATTERNS, CATALOG)
    assert m["machines"]["robot_a"]["signals"] == {"mission": "ns=2;i=1", "busy": "ns=2;i=2"}


def test_ambiguous_or_missing_pattern_fails():
    bad = {"s1": CATALOG["s1"] + [{"path": "Objects/Y/Busy", "node_id": "ns=2;i=3"}]}
    with pytest.raises(ValueError, match="2 nodes"):
        resolve(PATTERNS, bad)
    with pytest.raises(ValueError, match="0 nodes"):
        resolve(PATTERNS, {"s1": []})


def test_never_writes_outside_local(tmp_path):
    with pytest.raises(ValueError):
        write_local({"machines": {}}, tmp_path / "mapping.json")
    with pytest.raises(ValueError):
        write_local({"machines": {}}, LOCAL_DIR.parent / "data" / "mapping.json")
