import json
from collections import Counter

from pmlab.abstraction import abstract
from pmlab.events import Event, read_events
from pmlab.orders import correlate
from pmlab.recipes import UNIT_ROOT, load_recipes
from pmlab.rules import derive_extra

ORDERS = UNIT_ROOT / "data" / "orders"
LOGS = UNIT_ROOT / "data" / "logs"


def run(path):
    _, events = read_events(path)
    events = derive_extra(events)
    return events, abstract(events, load_recipes(), correlate(events))


def completes(entries, case):
    return [e.activity for e in entries if e.case_id == case and e.lifecycle == "complete"]


def test_abstract_ref_order():
    _, entries = run(ORDERS / "ref-order.jsonl")
    assert {e.case_id for e in entries} == {"order:1"}
    acts = completes(entries, "order:1")
    assert acts[:3] == ["reserve_pallet", "load_board", "load_covers"]
    count = Counter(acts)
    assert count["check_covers"] == 2
    assert count["bin_covers"] == 1 and count["reload_covers"] == 1
    assert count["assemble_gadget"] == 1                     # four assembly pairs, one operation
    assemble = [e for e in entries if e.activity == "assemble_gadget"]
    assert [(e.lifecycle, e.time) for e in assemble] == [("start", 748.5), ("complete", 879.3)]
    assert not [a for a in acts if a.startswith("unmapped:")]
    engrave = [e for e in entries if e.activity == "engrave_gadget"]
    assert [e.lifecycle for e in engrave] == ["start"]
    assert engrave[0].time == 918.0
    assert all(e.claim_kind == "inferred" for e in entries)
    times = [(e.time) for e in entries]
    assert times == sorted(times)


def test_entries_cite_every_event():
    events, entries = run(ORDERS / "ref-order.jsonl")
    cited = {i for e in entries for i in e.source_ids}
    assert {e.event_id for e in events} == cited
    starts = {e.activity: e for e in entries if e.lifecycle == "start"}
    assert starts["reserve_pallet"].time == 209.0            # the stay start, not its end
    assert "pallet:9" in starts["reserve_pallet"].objects


def mission(eid, activity, time, name):
    return Event(eid, activity, "robot_b", time, None, "observed", {"mission": name}, ())


def test_unmapped_kept():
    events = [mission("e1", "mission_started", 10.0, "dance"), mission("e2", "mission_ended", 20.0, "dance")]
    entries = abstract(events, load_recipes(), {"e1": "order:1", "e2": "order:1"})
    assert len(entries) == 1
    entry = entries[0]
    assert entry.activity == "unmapped:mission"
    assert entry.case_id == "order:1"
    assert entry.source_ids == ("e1", "e2")
    assert entry.lifecycle == "complete"


def test_abstract_train_matches_truth():
    """Orders with no deviation: the found operations are the true operations."""
    _, entries = run(LOGS / "train.jsonl")
    truth = json.loads((LOGS / "train.truth.json").read_text(encoding="utf-8"))
    by_case = {}
    for e in entries:
        if e.lifecycle == "complete":
            by_case.setdefault(e.case_id, []).append(e)
    clean = [o for o in truth["orders"].values() if not o["deviations"]]
    right = 0
    for order in clean:
        first = order["event_ids"][0]
        case = next((c for c, es in by_case.items() if any(first in e.source_ids for e in es)), None)
        found = Counter(e.activity for e in by_case.get(case, []))
        right += found == Counter(op["name"] for op in order["operations"])
    assert right == len(clean), (right, len(clean))
