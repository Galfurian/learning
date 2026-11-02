from pmlab.events import Event
from pmlab.rules import derive_extra


def ev(eid, activity, resource, time, pallet=None, **attrs):
    return Event(eid, activity, resource, time, pallet, "observed", attrs, ())


def stay(eid, bay, pallet, start, end):
    return Event(eid, "bay_stay", "conveyor", end, pallet, "derived",
                 {"bay": bay, "start": start, "corroborated": True}, ())


def signal(eid, time, old, new):
    return ev(eid, "signal_changed", "mill_cell", time, signal="program_running", old=old, new=new, program="engrave")


def test_program_events():
    events = [signal("e1", 10.0, False, True), signal("e2", 50.0, True, False),
              ev("e3", "signal_changed", "mill_cell", 60.0, signal="door_open", old=False, new=True)]
    out = derive_extra(events)
    started = [e for e in out if e.activity == "program_started"]
    ended = [e for e in out if e.activity == "program_ended"]
    assert len(started) == 1 and len(ended) == 1
    assert started[0].evidence == ("e1",) and started[0].time == 10.0
    assert ended[0].evidence == ("e2",) and ended[0].time == 50.0
    for e in started + ended:
        assert e.claim_kind == "derived"
        assert e.resource == "mill_cell"
        assert e.attrs["program"] == "engrave"
    assert {e.event_id for e in events} <= {e.event_id for e in out}
    assert len({e.event_id for e in out}) == len(out)
    assert [(e.time, int(e.event_id[1:])) for e in out] == sorted((e.time, int(e.event_id[1:])) for e in out)


def test_program_needs_a_change():
    """true -> true is no start; only a change of the value counts."""
    out = derive_extra([signal("e1", 10.0, True, True)])
    assert not [e for e in out if e.activity.startswith("program_")]


def test_cell_link_one_stay():
    events = [stay("e1", "assembly", 4, 0.0, 100.0), ev("e2", "operation_started", "assembly_cell", 20.0,
                                                        operation="assemble_gadget")]
    out = {e.event_id: e for e in derive_extra(events)}
    assert out["e2"].pallet == 4
    assert out["e2"].claim_kind == "inferred"
    assert "e1" in out["e2"].evidence


def test_cell_link_ambiguous():
    events = [stay("e1", "assembly", 4, 0.0, 100.0), stay("e2", "assembly", 6, 50.0, 150.0),
              ev("e3", "operation_done", "assembly_cell", 70.0, operation="assemble_gadget"),
              ev("e4", "operation_done", "assembly_cell", 200.0, operation="assemble_gadget"),
              ev("e5", "operation_done", "mill_cell", 20.0, operation="assemble_gadget")]
    out = {e.event_id: e for e in derive_extra(events)}
    assert out["e3"].pallet is None and out["e3"].claim_kind == "observed"   # two stays
    assert out["e4"].pallet is None                                          # no stay
    assert out["e5"].pallet is None                                          # the wrong bay


def test_cell_link_duplicate_stay():
    """Two copies of one stay (a duplicate record) are one stay, not two."""
    events = [stay("e1", "mill", 4, 0.0, 100.0), stay("e2", "mill", 4, 0.0, 100.0),
              signal("e3", 20.0, False, True)]
    out = derive_extra(events)
    started = next(e for e in out if e.activity == "program_started")
    assert started.pallet == 4 and started.claim_kind == "inferred"
    assert started.evidence == ("e3", "e1")
