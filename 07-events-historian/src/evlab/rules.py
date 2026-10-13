"""Signals -> events, and the cleaning before it.

clean(): which changes are real changes. derive(): versioned rules that turn
changes into domain events, each with its evidence (change ids) and its claim
kind:

- observed: one change, read as it is ("robot_a.mission became go_to_bin");
- derived: a rule over several changes that name the same thing ("a QC check
  failed": the check mission ended and the fault counter went up).

No rule here names a pallet that the signals do not name. Attaching a QC
result or a robot mission to a pallet is an inference (cases.py).
"""

from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field

from .records import Change, Event

RULES_VERSION = "1"


# ---------------------------------------------------------------- cleaning

@dataclass
class CleanReport:
    kept: int = 0
    dropped: Counter = field(default_factory=Counter)   # reason -> count
    initial: dict[str, object] = field(default_factory=dict)  # signal -> its first value (a state, not an event)


def clean(changes: Sequence[Change]) -> tuple[list[Change], CleanReport]:
    """Keep the changes that change something.

    - the first value of a signal (old is None) is the initial state, not an event;
    - a value equal to the last kept value is not a change (a duplicate notification, or a replay
      that writes the same value again);
    - a new replay cycle restarts the state: the first value after it is initial again;
    - a change without an event time (and its bounds) is dropped: nothing downstream may order it.
    Arrival order is kept; event-time order is not assumed (bounds can overlap).
    """
    report = CleanReport()
    last: dict[str, object] = {}
    cycle: int | None = None
    out = []
    for c in sorted(changes, key=lambda c: c.arrival_seq):
        if cycle is not None and c.replay_cycle != cycle:
            last.clear()
            report.dropped["replay boundary"] += 0   # a marker: the state restarts
        cycle = c.replay_cycle
        if c.event_time is None or c.event_time_lo is None or c.event_time_hi is None:
            report.dropped["no event time"] += 1   # a line clock that was not validated: no event, no order
            continue
        if c.signal not in last:
            last[c.signal] = c.new
            report.initial.setdefault(c.signal, c.new)
            report.dropped["initial value"] += 1
            continue
        if c.new == last[c.signal]:
            report.dropped["unchanged or duplicate"] += 1
            continue
        last[c.signal] = c.new
        out.append(c)
    report.kept = len(out)
    return out, report


# ---------------------------------------------------------------- rules

class _Builder:
    def __init__(self) -> None:
        self.events: list[Event] = []

    def add(self, activity: str, resource: str, changes: Sequence[Change], rule: str, kind: str, *,
            pallet: int | None = None, **attrs) -> None:
        anchor = changes[-1]
        self.events.append(Event(
            event_id=f"e{len(self.events) + 1}", activity=activity, resource=resource,
            event_time=anchor.event_time, event_time_lo=min(c.event_time_lo for c in changes),
            event_time_hi=max(c.event_time_hi for c in changes), evidence=tuple(c.change_id for c in changes),
            rule=rule, rule_version=RULES_VERSION, claim_kind=kind, pallet=pallet, attrs=attrs))


def _field(signal: str) -> str:
    return signal.split(".", 1)[1]


def derive(changes: Iterable[Change]) -> list[Event]:
    """Clean changes (from clean()) -> events, ordered by their first evidence (arrival order)."""
    changes_list = list(changes)
    changes = changes_list
    b = _Builder()
    mission: dict[str, tuple[str, Change]] = {}            # machine -> (running mission, its start change)
    segment: dict[str, set[int]] = {}                       # "segment3" -> pallets in it
    slots: dict[str, int] = {}                              # "conveyor.segment3.item1" -> pallet
    for c in changes:
        f = _field(c.signal)
        # missions: one change says it, so the event is observed
        if f == "mission":
            if c.old:
                b.add("mission_ended", c.machine, [c], "missions", "observed", mission=c.old)
            if c.new:
                b.add("mission_started", c.machine, [c], "missions", "observed", mission=c.new)
                mission[c.machine] = (c.new, c)
        elif c.machine == "tester" and f == "last_result" and c.new:
            b.add("test_result", c.machine, [c], "tester", "observed", result=c.new)
        # conveyor: an assignment is not a movement
        elif f.startswith("destination."):
            bay = f.split(".", 1)[1]
            if c.new:
                b.add("destination_assigned", c.machine, [c], "destinations", "observed", pallet=int(c.new), stop=bay)
            elif c.old:
                b.add("destination_cleared", c.machine, [c], "destinations", "observed", pallet=int(c.old), stop=bay)
        elif f.startswith("segment"):
            seg = f.split(".")[0]
            slots[c.signal] = int(c.new or 0)
            now = {p for s, p in slots.items() if s.startswith(f"conveyor.{seg}.") and p}
            before = segment.get(seg, set())
            for p in sorted(now - before):
                b.add("pallet_entered_segment", c.machine, [c], "segments", "observed", pallet=p, segment=seg)
            for p in sorted(before - now):
                b.add("pallet_left_segment", c.machine, [c], "segments", "observed", pallet=p, segment=seg)
            segment[seg] = now
        elif c.machine == "mill_cell" and f == "alarm_message":
            new = set(c.new or []) if isinstance(c.new, list) else set()
            old = set(c.old or []) if isinstance(c.old, list) else set()
            for code in sorted(new - old, key=str):
                b.add("alarm_raised", c.machine, [c], "alarms", "observed", code=code)
            for code in sorted(old - new, key=str):
                b.add("alarm_cleared", c.machine, [c], "alarms", "observed", code=code)
        elif c.machine == "assembly_cell" and f in ("operation_running", "operation_done") and c.new is True:
            b.add("operation_started" if f == "operation_running" else "operation_done", c.machine, [c],
                  "assembly", "observed")
    _qc_checks(b, changes_list)
    b.events = _drop_shuffles(b.events)
    b.events.sort(key=lambda e: int(min(e.evidence, key=lambda x: int(x[1:]))[1:]))
    for i, e in enumerate(b.events, start=1):
        object.__setattr__(e, "event_id", f"e{i}")
    return b.events


SHUFFLE_S = 0.3   # a FIFO rewrites its slots one by one: a pallet "leaves" and "enters" the same segment


def _drop_shuffles(events: list[Event]) -> list[Event]:
    """Drop a leave/enter pair of the same pallet and segment within SHUFFLE_S: a slot rewrite, not a movement."""
    drop = set()
    seg = [e for e in events if e.activity in ("pallet_left_segment", "pallet_entered_segment")]
    for i, a in enumerate(seg):
        if id(a) in drop:
            continue
        for x in seg[i + 1:]:
            if x.event_time - a.event_time > SHUFFLE_S:
                break
            if (id(x) not in drop and x.pallet == a.pallet and x.attrs["segment"] == a.attrs["segment"]
                    and x.activity != a.activity):
                drop.update((id(a), id(x)))
                break
    return [e for e in events if id(e) not in drop]


QC_GRACE_S = 1.0   # result signals may arrive up to this long after the check mission ends


def _qc_checks(b: "_Builder", changes: Sequence[Change]) -> None:
    """One QC check = the check mission from start to end. Its result is in the signals around it:
    the fault counter went up -> failed; else the result flag or the check counter -> passed.
    Nothing in the window -> the result is unknown, and the rule says so."""
    qc = [c for c in changes if c.machine == "qc_station"]
    start = None
    for c in qc:
        if _field(c.signal) != "mission":
            continue
        if c.new == "check_object":
            start = c
        elif c.old == "check_object" and start is not None:
            lo, hi = start.event_time_lo, c.event_time_hi + QC_GRACE_S
            window = [x for x in qc if lo <= x.event_time <= hi and x.signal != "qc_station.mission"]
            faults = [x for x in window if _field(x.signal) == "faults_total" and (x.new or 0) > (x.old or 0)]
            flag = [x for x in window if _field(x.signal) == "last_result"]
            counted = [x for x in window if _field(x.signal) == "checks_total"]
            if faults:
                b.add("check_failed", "qc_station", [start, c, faults[0]], "qc_checks", "derived")
            elif flag and flag[-1].new is False:
                b.add("check_failed", "qc_station", [start, c, flag[-1]], "qc_checks", "derived")
            elif flag or counted:
                b.add("check_passed", "qc_station", [start, c, *(flag or counted)[-1:]], "qc_checks", "derived")
            else:
                b.add("check_result_unknown", "qc_station", [start, c], "qc_checks", "derived")
            start = None
