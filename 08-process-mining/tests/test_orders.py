import json
from dataclasses import replace

from pmlab.events import read_events
from pmlab.orders import JOIN_S, correlate
from pmlab.recipes import UNIT_ROOT
from pmlab.rules import derive_extra

LOGS = UNIT_ROOT / "data" / "logs"
ORDERS = UNIT_ROOT / "data" / "orders"


def truth_map(truth):
    """event id -> true order. The events of an "extra" deviation belong to the order that repeats."""
    out = {}
    for oid, order in truth["orders"].items():
        for eid in order["event_ids"]:
            out[eid] = oid
        for dev in order["deviations"]:
            for eid in dev["event_ids"]:
                out.setdefault(eid, oid)
    return out


def train():
    _, events = read_events(LOGS / "train.jsonl")
    truth = json.loads((LOGS / "train.truth.json").read_text(encoding="utf-8"))
    return events, truth


def same_partition(found, truth, ids):
    """Precision: of the placed events, the share whose found order holds the same events as
    the true order (the order names differ). Coverage: the share of events placed."""
    by_found = {}
    for eid in ids:
        if eid in found:
            by_found.setdefault(found[eid], []).append(eid)
    # each found order is named after the true order of most of its events
    name = {}
    for oid, members in by_found.items():
        votes = {}
        for eid in members:
            votes[truth.get(eid)] = votes.get(truth.get(eid), 0) + 1
        name[oid] = max(votes, key=votes.get)
    placed = [eid for eid in ids if eid in found]
    right = sum(1 for eid in placed if name[found[eid]] == truth.get(eid))
    return right / len(placed), len(placed) / len(ids)


def test_correlation_accuracy():
    events, truth = train()
    found = correlate(derive_extra(events))
    tmap = truth_map(truth)
    ids = [e.event_id for e in events]
    assert set(tmap) == set(ids)
    precision, coverage = same_partition(found, tmap, ids)
    assert precision >= 0.98, precision
    assert coverage >= 0.90, coverage
    assert all(v.startswith("order:") for v in found.values())
    # one found order per true order, no merge of two true orders
    names = {}
    for eid, oid in found.items():
        if eid in tmap:
            names.setdefault(oid, set()).add(tmap[eid])
    assert sum(len(v) > 1 for v in names.values()) <= 0.02 * len(names)


def span(truth_order, by_id):
    times = [by_id[eid].time for eid in truth_order["event_ids"]]
    return min(times), max(times)


def test_reused_pallet_not_merged():
    events, truth = train()
    by_id = {e.event_id: e for e in events}
    users = [(oid, o) for oid, o in truth["orders"].items() if 3 in o["pallets"]]
    pairs = []
    for i, (a, oa) in enumerate(users):
        for b, ob in users[i + 1:]:
            (sa, ea), (sb, eb) = span(oa, by_id), span(ob, by_id)
            if sa < eb and sb < ea:
                pairs.append((a, b))
    assert pairs, "the train log has two overlapping orders that use pallet 3"
    found = correlate(derive_extra(events))
    for a, b in pairs:
        stays = {}
        for oid in (a, b):
            stays[oid] = {eid for eid in truth["orders"][oid]["event_ids"]
                          if by_id[eid].activity == "bay_stay" and by_id[eid].pallet == 3}
            assert stays[oid]
        found_a = {found.get(eid) for eid in stays[a]}
        found_b = {found.get(eid) for eid in stays[b]}
        assert len(found_a) == 1 and len(found_b) == 1 and None not in found_a | found_b
        assert found_a.isdisjoint(found_b)


def test_reload_joins_failed_order():
    _, events = read_events(ORDERS / "ref-order.jsonl")
    found = correlate(derive_extra(events))
    stays = {p: {found.get(e.event_id) for e in events if e.activity == "bay_stay" and e.pallet == p}
             for p in (7, 8, 9)}
    assert stays[7] == stays[8] == stays[9] == {"order:1"}
    assert set(found.values()) == {"order:1"}
    assert all(e.event_id in found for e in events)


def test_no_guess_without_a_load():
    """A stay of a pallet that no burst loaded stays out."""
    _, events = read_events(ORDERS / "ref-order.jsonl")
    late = [e for e in events if e.time > 700.0]
    found = correlate(late)
    assert not found


def shift_after(events, time, delta):
    """Move every event after `time` (and the start of its stay) `delta` seconds later."""
    out = []
    for e in events:
        if e.time > time:
            attrs = dict(e.attrs)
            if e.activity == "bay_stay":
                attrs["start"] += delta
            e = replace(e, time=e.time + delta, attrs=attrs)
        out.append(e)
    return out


def test_burst_gap_above_join_splits():
    """Where the burst rule breaks: in ref-order the covers load starts 1.6 s after the board load.
    With a gap above JOIN_S the two loads are two bursts, so one order becomes two. The documented
    outcome: a split (the board pallet in one order, the covers pallets in the other), no wrong merge."""
    _, events = read_events(ORDERS / "ref-order.jsonl")
    board_end = max(e.time for e in events if e.attrs.get("mission") == "place_board_on_pallet")
    events = shift_after(events, board_end, JOIN_S + 2.0)
    found = correlate(derive_extra(events))
    pallet_order = {p: {found.get(e.event_id) for e in events if e.activity == "bay_stay" and e.pallet == p}
                    for p in (7, 8, 9)}
    assert pallet_order[9] == {"order:1"}
    assert pallet_order[7] == pallet_order[8] == {"order:2"}      # the reload still joins the failed pallet
    assert set(found.values()) == {"order:1", "order:2"}
