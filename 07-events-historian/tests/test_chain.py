from evlab.chain import chain, describe, in_loop
from evlab.records import Event


def ev(i, t, activity, resource="conveyor", pallet=None, case="p7#1", kind="observed", **attrs):
    return Event(f"e{i}", activity, resource, t, t - 0.1, t + 0.1, (f"c{i}",), "r", "1", kind, pallet, case, attrs)


LOOP = [ev(1, 10, "pallet_entered_segment", pallet=7, segment="segment3"),
        ev(2, 20, "pallet_left_segment", pallet=7, segment="segment3"),
        ev(3, 60, "pallet_entered_segment", pallet=7, segment="segment6")]


def test_in_loop():
    assert in_loop(7, 15, LOOP) is True
    assert in_loop(7, 40, LOOP) is False
    assert in_loop(7, 5, LOOP) is None


def test_visit_is_corroborated_only_when_off_the_loop():
    events = LOOP + [ev(4, 22, "destination_assigned", pallet=7, stop="bay4_1"),
                     ev(5, 50, "destination_cleared", pallet=7, stop="bay4_1"),
                     ev(6, 61, "destination_assigned", pallet=7, stop="bay3_1"),
                     ev(7, 80, "destination_cleared", pallet=7, stop="bay3_1"),
                     ev(8, 30, "check_failed", resource="qc_station", pallet=7, kind="inferred")]
    c = chain(events, "p7#1")
    assert [e.event_id for e in c.steps] == ["e4", "e8", "e5", "e6", "e7"]
    assert [(v.stop, v.corroborated) for v in c.visits] == [("bay4_1", True), ("bay3_1", False)]
    assert c.loop_events == 3 and "inferred" in c.coverage[0]
    assert "inferred link to the pallet" in describe(c.steps[1])


def test_unknown_case():
    c = chain(LOOP, "p9#1")
    assert c.steps == [] and c.coverage == ["no event of this case in the recording"]
