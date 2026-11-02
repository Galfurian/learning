"""Extra signal-to-event rules on top of the unit 07 export.

1. Program events: a `signal_changed` on `mill_cell` of the signal
   `program_running` from false to true is a `program_started`; from true
   to false it is a `program_ended`. The new event is `derived` and cites the
   change as evidence. The change event stays in the list.
2. Cell to pallet: an event of `assembly_cell` or `mill_cell` (the cell does
   not see the pallet) that falls inside exactly one bay stay of the bay of
   that cell gets the pallet of that stay. That is an inference: the claim
   becomes `inferred` and the stay is added to the evidence. Inside zero or
   two stays, the event keeps `pallet=None` (no guess). Two copies of one
   stay (a duplicate record) are one stay.
"""

from dataclasses import replace

from pmlab.events import Event

CELL_BAY = {"assembly_cell": "assembly", "mill_cell": "mill"}
PROGRAM = {(False, True): "program_started", (True, False): "program_ended"}
SIGNAL = "program_running"


def number(event_id: str) -> int:
    return int(event_id[1:])


def order_key(event: Event) -> tuple[float, int]:
    return event.time, number(event.event_id)


def stay_span(event: Event) -> tuple[float, float]:
    """A bay stay is recorded at its end; attrs.start is its begin."""
    return float(event.attrs["start"]), event.time


def stays_at(events: list[Event], bay: str, time: float) -> list[Event]:
    """The bay stays at `bay` whose interval holds `time` (bounds included). Copies of one stay
    (same pallet, start and end: a duplicate record) count once; the first copy is kept."""
    out: dict[tuple, Event] = {}
    for e in events:
        if e.activity == "bay_stay" and e.attrs.get("bay") == bay:
            start, end = stay_span(e)
            if start <= time <= end:
                out.setdefault((e.pallet, start, end), e)
    return list(out.values())


def _programs(events: list[Event]) -> list[Event]:
    cited = {i for e in events if e.activity in PROGRAM.values() for i in e.evidence}
    next_id = max((number(e.event_id) for e in events), default=0) + 1
    out = []
    for e in sorted(events, key=order_key):
        if e.activity != "signal_changed" or e.resource != "mill_cell" or e.attrs.get("signal") != SIGNAL:
            continue
        name = PROGRAM.get((bool(e.attrs.get("old")), bool(e.attrs.get("new"))))
        if name is None or e.event_id in cited:
            continue
        attrs = {k: v for k, v in e.attrs.items() if k not in ("signal", "old", "new")}
        out.append(Event(f"e{next_id}", name, e.resource, e.time, e.pallet, "derived", attrs, (e.event_id,)))
        next_id += 1
    return out


def _link(event: Event, stays: list[Event]) -> Event:
    if event.resource not in CELL_BAY or event.pallet is not None:
        return event
    found = stays_at(stays, CELL_BAY[event.resource], event.time)
    if len(found) != 1:
        return event
    stay = found[0]
    return replace(event, pallet=stay.pallet, claim_kind="inferred", evidence=event.evidence + (stay.event_id,))


def derive_extra(events: list[Event]) -> list[Event]:
    """All events plus the program events, cell events linked to a pallet, sorted by (time, id)."""
    events = list(events) + _programs(events)
    stays = [e for e in events if e.activity == "bay_stay" and e.pallet is not None]
    return sorted((_link(e, stays) for e in events), key=order_key)
