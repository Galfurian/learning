"""The evidence chain of one case: what happened to one pallet in one product cycle, and how we know.

A chain is the case's events in time order, with three additions:

- each destination assignment says whether the pallet really went there.
  An assignment is an intention. It is corroborated when the pallet is absent
  from the conveyor loop while assigned: it left the loop for that stop;
- the segment events are evidence, not steps: they are counted, not listed;
- a coverage list says what the recording cannot show (no signal names the
  pallet at a robot or at the QC station: those links are inferred).
"""

from collections.abc import Sequence
from dataclasses import dataclass, field

from .records import Event

LOOP_ACTIVITIES = ("pallet_entered_segment", "pallet_left_segment")


@dataclass
class Visit:
    stop: str
    assigned: Event
    cleared: Event | None
    corroborated: bool
    evidence: list[str]           # event ids that support or deny the visit
    note: str


@dataclass
class Chain:
    case_id: str
    pallet: int | None
    steps: list[Event]
    visits: list[Visit]
    loop_events: int
    coverage: list[str] = field(default_factory=list)

    @property
    def ids(self) -> list[str]:
        return [e.event_id for e in self.steps]


def in_loop(pallet: int, t: float, loop: Sequence[Event]) -> bool | None:
    """Is the pallet on the loop at time t? None if no loop event of it comes before t."""
    last = None
    for e in loop:
        if e.pallet == pallet and e.event_time <= t:
            last = e
    if last is None:
        return None
    if last.activity == "pallet_entered_segment":
        return True
    # it left a segment: it is on the loop if it entered another one at the same moment
    return any(e.pallet == pallet and e.activity == "pallet_entered_segment"
               and abs(e.event_time - last.event_time) < 1.0 for e in loop)


def visits(pallet: int, steps: Sequence[Event], loop: Sequence[Event]) -> list[Visit]:
    out = []
    for i, a in enumerate(steps):
        if a.activity != "destination_assigned":
            continue
        stop = a.attrs.get("stop")
        cleared = next((c for c in steps[i + 1:] if c.activity == "destination_cleared" and c.attrs.get("stop") == stop),
                       None)
        if cleared is None:
            out.append(Visit(stop, a, None, False, [a.event_id], "assigned, never cleared in the recording"))
            continue
        mid = (a.event_time + cleared.event_time) / 2
        on = in_loop(pallet, mid, loop)
        if on is False:
            out.append(Visit(stop, a, cleared, True, [a.event_id, cleared.event_id],
                             "off the loop while assigned: it was at the stop"))
        elif on is True:
            out.append(Visit(stop, a, cleared, False, [a.event_id, cleared.event_id],
                             "still on the loop while assigned: assignment only"))
        else:
            out.append(Visit(stop, a, cleared, False, [a.event_id, cleared.event_id],
                             "no loop record of this pallet: not corroborated"))
    return out


def chain(events: Sequence[Event], case_id: str) -> Chain:
    """The case's events (case_id set by cases.assign_cases) in time order."""
    mine = sorted((e for e in events if e.case_id == case_id), key=lambda e: e.event_time)
    pallet = next((e.pallet for e in mine if e.pallet is not None), None)
    loop = sorted((e for e in events if e.activity in LOOP_ACTIVITIES and e.pallet == pallet),
                  key=lambda e: e.event_time)
    steps = [e for e in mine if e.activity not in LOOP_ACTIVITIES]
    c = Chain(case_id, pallet, steps, visits(pallet, steps, loop) if pallet is not None else [],
              sum(1 for e in mine if e.activity in LOOP_ACTIVITIES))
    if any(e.claim_kind == "inferred" for e in steps):
        c.coverage.append("no signal names the pallet at the QC station or at a robot: those links are inferred "
                          "from the time the pallet was at the QC bay")
    if not steps:
        c.coverage.append("no event of this case in the recording")
    return c


def describe(e: Event) -> str:
    """One line a reader (or a generator) can cite."""
    what = {
        "mission_started": "started mission {mission}", "mission_ended": "ended mission {mission}",
        "check_failed": "QC check failed", "check_passed": "QC check passed",
        "check_result_unknown": "QC check result not recorded",
        "destination_assigned": "pallet {pallet} assigned to stop {stop}",
        "destination_cleared": "pallet {pallet} released from stop {stop}",
        "test_result": "test result {result}", "alarm_raised": "alarm {code} raised", "alarm_cleared": "alarm {code} cleared",
        "operation_started": "operation started", "operation_done": "operation done",
    }.get(e.activity, e.activity)
    text = what.format(pallet=e.pallet, **e.attrs) if "{" in what else what
    kind = e.claim_kind if e.claim_kind != "inferred" else "inferred link to the pallet"
    return f"[{e.event_id}] t={e.event_time:.1f} s · {e.resource}: {text} ({kind})"


# The role of each bay on the line (logical layout, not a signal).
BAYS = {"bay1": "tester bay", "bay2": "mill bay", "bay3": "assembly bay", "bay4": "QC bay", "bay5": "load/unload bay"}


def bay(stop: str) -> str:
    return stop.split("_")[0]


def story(c: Chain) -> list[str]:
    """The chain compressed for a reader: one line per stay at a bay, one line per mission, one per result.

    Each line keeps the ids of the events it summarizes, so a citation still points at evidence.
    """
    lines: list[tuple[float, str]] = []
    # stays: consecutive corroborated visits to positions of the same bay become one stay
    stays: list[list[Visit]] = []
    for v in c.visits:
        if stays and bay(stays[-1][-1].stop) == bay(v.stop) and v.corroborated == stays[-1][-1].corroborated:
            stays[-1].append(v)
        else:
            stays.append([v])
    for group in stays:
        first, last = group[0], group[-1]
        end = last.cleared.event_time if last.cleared else None
        ids = ", ".join(sorted({first.assigned.event_id, *(x.cleared.event_id for x in group if x.cleared)},
                               key=lambda i: int(i[1:])))
        where = BAYS.get(bay(first.stop), bay(first.stop))
        span = f"from t={first.assigned.event_time:.0f} s" + (f" to t={end:.0f} s" if end is not None else "")
        status = "was at" if first.corroborated else "was assigned to (not shown that it went to)"
        lines.append((first.assigned.event_time, f"[{ids}] pallet {c.pallet} {status} the {where} {span} (observed)"))
    # missions: start and end of the same mission on the same resource become one line
    open_: dict[str, Event] = {}
    for e in c.steps:
        if e.activity == "mission_started":
            open_[e.resource] = e
        elif e.activity == "mission_ended":
            s = open_.get(e.resource)
            s = open_.pop(e.resource) if s is not None and s.attrs.get("mission") == e.attrs.get("mission") else None
            ids = f"{s.event_id}, {e.event_id}" if s else e.event_id
            t0 = s.event_time if s else e.event_time
            kind = "inferred link to the pallet" if (e.claim_kind == "inferred" or (s and s.claim_kind == "inferred")) \
                else e.claim_kind
            lines.append((t0, f"[{ids}] {e.resource} did {e.attrs.get('mission')} from t={t0:.0f} s to "
                               f"t={e.event_time:.0f} s ({kind})"))
        elif e.activity not in ("destination_assigned", "destination_cleared"):
            lines.append((e.event_time, describe(e)))
    for s in open_.values():
        lines.append((s.event_time, f"[{s.event_id}] {s.resource} started {s.attrs.get('mission')} at "
                                    f"t={s.event_time:.0f} s; its end is not linked to this pallet ({s.claim_kind})"))
    return [text for _, text in sorted(lines, key=lambda x: x[0])] + [f"(coverage) {n}" for n in c.coverage]
