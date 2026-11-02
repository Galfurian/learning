import random

from helpers import entries_of

from pmlab.log import Entry, to_log, variants
from pmlab.rules import number


def test_pallet_notion_synthetic_duplication():
    # An entry goes to every pallet in its objects: a two-pallet entry is
    # counted twice, an entry without a pallet is in no pallet trace.
    entries = [
        Entry("order:1", "a", "complete", 1.0, "r", ("order:1", "pallet:1"), ("e1",), "derived"),
        Entry("order:1", "b", "complete", 2.0, "r", ("order:1", "pallet:1", "pallet:2"), ("e2",), "derived"),
        Entry("order:1", "c", "complete", 3.0, "r", ("order:1",), ("e3",), "derived"),
    ]
    by_pallet = {t.case_id: t.activities for t in to_log(entries, "pallet")}
    assert by_pallet == {"pallet:1": ("a", "b"), "pallet:2": ("b",)}
    assert sum(len(t.entries) for t in to_log(entries, "order")) == 3


def test_pallet_notion_duplicates():
    entries = entries_of("train")
    n_order = sum(len(t.entries) for t in to_log(entries, "order"))
    n_pallet = sum(len(t.entries) for t in to_log(entries, "pallet"))
    pallets = [sum(o.startswith("pallet:") for o in e.objects) for e in entries]
    assert any(p >= 2 for p in pallets)
    # difference = extra copies of entries with two or more pallets,
    # minus the entries that have no pallet at all
    assert n_pallet - n_order == sum(p - 1 for p in pallets if p >= 2) - pallets.count(0)


def test_same_time_order():
    entries = [
        Entry("order:1", "a", "complete", 5.0, "r", ("order:1",), (f"e{i}",), "derived")
        for i in (12, 3, 101, 7)
    ]
    expected = ["e3", "e7", "e12", "e101"]
    for seed in (1, 2):
        shuffled = entries[:]
        random.Random(seed).shuffle(shuffled)
        (trace,) = to_log(shuffled)
        assert [e.source_ids[0] for e in trace.entries] == expected
    for t in to_log(entries_of("train")):
        keys = [(e.time, number(e.source_ids[0])) for e in t.entries]
        assert keys == sorted(keys)


def test_variants_and_activities():
    traces = to_log(entries_of("ref-order"))
    assert len(traces) == 1
    assert traces[0].activities == tuple(e.activity for e in traces[0].entries if e.lifecycle == "complete")
    assert sum(variants(traces).values()) == 1
