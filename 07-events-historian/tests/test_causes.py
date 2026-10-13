from evlab.causes import explain, explanation_lines
from evlab.chain import Chain
from evlab.records import Event


def ev(i, t, activity, resource, kind="inferred", **attrs):
    return Event(f"e{i}", activity, resource, t, t, t, (f"c{i}",), "r", "1", kind, 7, "p7#1", attrs)


def chain(*steps):
    return Chain("p7#1", 7, list(steps), [], 0)


def test_rework_rule():
    c = chain(ev(1, 10, "check_failed", "qc_station"),
              ev(2, 20, "mission_started", "robot_b", mission="take_cover_top_from_pallet"),
              ev(3, 40, "mission_started", "robot_b", mission="drop_covers_in_bin"))
    [x] = explain(c)
    assert x.cause == ["e1"] and x.effect == ["e2", "e3"] and x.claim_kind == "inferred"
    assert "rework" in explanation_lines(c)[0]


def test_no_rule_no_cause():
    c = chain(ev(1, 10, "check_passed", "qc_station"))
    assert explain(c) == [] and "not why" in explanation_lines(c)[0]
    c = chain(ev(1, 10, "check_failed", "qc_station"))      # failed, but no rework seen
    assert explain(c) == []
