"""Object-centric log: events with many objects, flattening and OCEL 2.0 JSON.

This module does not import pm4py. Tests read the JSON back with pm4py.
"""

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from pmlab.log import Entry, Trace, sort_key

EPOCH = datetime(2026, 1, 1, tzinfo=timezone.utc)   # time 0.0 of the log; times are seconds from it
TYPES = ("order", "pallet", "resource")


def object_type(obj: str) -> str:
    """Type of an object id: order, pallet, or resource (all other ids)."""
    kind = obj.split(":", 1)[0]
    return kind if ":" in obj and kind in ("order", "pallet") else "resource"


@dataclass
class OCEL:
    objects: dict[str, str]     # id -> type ("order", "pallet", "resource")
    events: list[Entry]


def ocel(entries: list[Entry]) -> OCEL:
    """Build the object-centric log. The resource of an entry is always an object."""
    objects: dict[str, str] = {}
    for e in entries:
        for obj in (*e.objects, e.resource):
            objects[obj] = object_type(obj)
    return OCEL(objects, sorted(entries, key=sort_key))


def flatten(o: OCEL, object_type: str) -> list[Trace]:
    """One trace per object of the type, holding every event that references it.

    An event with two pallets goes into both pallet traces: that copy is
    the convergence. Traces sort by case id (length, then text).
    """
    if object_type not in TYPES:
        raise ValueError(f"unknown object type: {object_type}")
    groups: dict[str, list[Entry]] = defaultdict(list)
    for e in o.events:
        for obj in {*e.objects, e.resource}:
            if o.objects[obj] == object_type:
                groups[obj].append(e)
    return [Trace(c, es) for c, es in sorted(groups.items(), key=lambda kv: (len(kv[0]), kv[0]))]


def flattening_errors(o: OCEL, object_type: str) -> dict[str, int]:
    """Count the two flattening errors for a case type.

    convergence: number of events copied into two or more cases of the type
    (events are counted once, not once per copy).

    divergence: number of (case, activity) pairs where the case holds two or
    more complete instances of the activity and their "other objects" differ.
    The other objects of an event are its objects that are neither of the
    case type nor resources: orders for pallet cases, pallets for order cases.
    Example: one pallet reused by two orders gives divergence in its case.
    """
    traces = flatten(o, object_type)
    copies: dict[int, int] = defaultdict(int)
    for t in traces:
        for e in t.entries:
            copies[id(e)] += 1
    convergence = sum(1 for n in copies.values() if n >= 2)
    divergence = 0
    for t in traces:
        seen: dict[str, set[frozenset[str]]] = defaultdict(set)
        count: dict[str, int] = defaultdict(int)
        for e in t.entries:
            if e.lifecycle != "complete":
                continue
            count[e.activity] += 1
            seen[e.activity].add(frozenset(x for x in e.objects if o.objects[x] not in (object_type, "resource")))
        divergence += sum(1 for a, n in count.items() if n >= 2 and len(seen[a]) >= 2)
    return {"convergence": convergence, "divergence": divergence}


def _event_id(e: Entry) -> str:
    return f"{e.case_id}/{e.activity}/{e.lifecycle}/{e.source_ids[0]}"


def to_ocel_json(o: OCEL) -> dict:
    """OCEL 2.0 JSON. Lifecycle, claim kind and resource are event attributes.

    Timestamps are ISO strings: 2026-01-01T00:00:00Z plus the entry time in seconds.
    """
    ev_types = sorted({e.activity for e in o.events})
    return {
        "objectTypes": [{"name": t, "attributes": []} for t in TYPES],
        "eventTypes": [
            {"name": a, "attributes": [{"name": n, "type": "string"} for n in ("lifecycle", "claim_kind", "resource")]}
            for a in ev_types
        ],
        "objects": [{"id": i, "type": t, "attributes": []} for i, t in sorted(o.objects.items())],
        "events": [
            {
                "id": _event_id(e),
                "type": e.activity,
                "time": (EPOCH + timedelta(seconds=e.time)).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
                "attributes": [
                    {"name": "lifecycle", "value": e.lifecycle},
                    {"name": "claim_kind", "value": e.claim_kind},
                    {"name": "resource", "value": e.resource},
                ],
                "relationships": [{"objectId": x, "qualifier": o.objects[x]} for x in sorted({*e.objects, e.resource})],
            }
            for e in o.events
        ],
    }
