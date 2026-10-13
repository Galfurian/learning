"""Assign product-cycle cases and make safe pallet correlations.

A destination assignment at bay 5 starts a product cycle.  The replay cycle
is provenance; it is not a product cycle.  QC and robot mission signals do
not carry a pallet id, so this module may attach one only through the
versioned, time-bounded bay correlation rule below.  Such an attachment is
always an ``inferred`` claim.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import replace

from .records import Event

CASES_VERSION = "2"
CORRELATION_RULE = "qc-bay-pallet"
CORRELATION_WINDOW_S = 60.0

_CORRELATED_MISSIONS = frozenset({
    "go_to_qc_bay",
    "take_cover_top_from_pallet",
    "take_cover_bottom_from_pallet",
    "go_to_bin",
    "drop_covers_in_bin",
})


def _case_id(pallet: int, cycle: int) -> str:
    return f"p{pallet}#{cycle}"


def _needs_correlation(event: Event) -> bool:
    if event.resource == "qc_station":
        return event.activity in {
            "check_failed",
            "check_passed",
            "check_result_unknown",
        } or event.attrs.get("mission") == "check_object"
    return (
        event.activity in {"mission_started", "mission_ended"}
        and event.attrs.get("mission") in _CORRELATED_MISSIONS
    )


def _time_distance(event: Event, marker: Event) -> float | None:
    if event.event_time is None or marker.event_time is None:
        return None
    return abs(event.event_time - marker.event_time)


@dataclass(frozen=True)
class _Occupancy:
    pallet: int
    case_id: str
    stop: str
    start: float
    end: float | None
    assignment: Event


def _inferred(event: Event, marker: Event, *, note: str) -> Event:
    return replace(
        event,
        pallet=marker.pallet,
        case_id=marker.case_id,
        rule=CORRELATION_RULE,
        rule_version=CASES_VERSION,
        claim_kind="inferred",
        confidence_note=note,
    )


def _occupancies(events: list[Event]) -> list[_Occupancy]:
    open_intervals: dict[tuple[int, str], list[_Occupancy]] = {}
    result: list[_Occupancy] = []
    for event in events:
        stop = str(event.attrs.get("stop", ""))
        if event.activity == "destination_assigned" and stop.startswith("bay4"):
            if event.pallet is not None and event.case_id is not None and event.event_time is not None:
                interval = _Occupancy(event.pallet, event.case_id, stop, event.event_time, None, event)
                open_intervals.setdefault((event.pallet, stop), []).append(interval)
                result.append(interval)
        elif event.activity == "destination_cleared" and stop.startswith("bay4"):
            if event.pallet is None or event.event_time is None:
                continue
            candidates = open_intervals.get((event.pallet, stop), [])
            if not candidates:
                continue
            previous = candidates.pop(0)
            result[result.index(previous)] = _Occupancy(
                previous.pallet, previous.case_id, previous.stop,
                previous.start, event.event_time, previous.assignment,
            )
    return result


def _occupancy_candidates(event: Event, occupancies: list[_Occupancy]) -> list[_Occupancy]:
    if event.event_time is None:
        return []
    candidates = [
        occupancy for occupancy in occupancies
        if occupancy.start <= event.event_time
        and (occupancy.end is None or event.event_time < occupancy.end)
    ]
    # Two bay positions of the same product are still one pallet, but two
    # product cases with the same pallet id are not interchangeable.
    unique: dict[str, _Occupancy] = {}
    for occupancy in candidates:
        unique.setdefault(occupancy.case_id, occupancy)
    return list(unique.values())


def _correlate_occupancy(event: Event, occupancies: list[_Occupancy]) -> tuple[Event, bool]:
    """Use an unambiguous bay-4 occupancy; bool says whether it was blocked."""
    candidates = _occupancy_candidates(event, occupancies)
    if len(candidates) != 1:
        return event, len(candidates) > 1
    occupancy = candidates[0]
    end = "open" if occupancy.end is None else f"{occupancy.end:g}s"
    note = (
        f"{CORRELATION_RULE} v{CASES_VERSION}: occupancy of {occupancy.stop} "
        f"for {occupancy.case_id} from {occupancy.start:g}s to {end}"
    )
    return _inferred(event, occupancy.assignment, note=note), False


def _correlate_fallback(event: Event, markers: list[Event]) -> tuple[Event, bool]:
    """Use the old assignment window only when occupancy gives no answer."""
    candidates: list[tuple[float, Event]] = []
    for marker in markers:
        distance = _time_distance(event, marker)
        if (
            distance is not None
            and marker.event_time is not None
            and event.event_time is not None
            and marker.event_time <= event.event_time
            and distance <= CORRELATION_WINDOW_S
        ):
            candidates.append((distance, marker))
    if not candidates:
        return event, False

    # A repeated assignment for the same case is harmless.  Different cases
    # in the window are ambiguous: abstain instead of choosing by proximity.
    by_case: dict[str, tuple[float, Event]] = {}
    for distance, marker in candidates:
        assert marker.case_id is not None
        previous = by_case.get(marker.case_id)
        if previous is None or distance < previous[0]:
            by_case[marker.case_id] = (distance, marker)
    if len(by_case) != 1:
        return event, True

    distance, marker = next(iter(by_case.values()))
    assert marker.case_id is not None and marker.pallet is not None
    return _inferred(
        event,
        marker,
        note=(
            f"{CORRELATION_RULE} v{CASES_VERSION}: fallback from {marker.attrs['stop']} "
            f"assignment for {marker.case_id}, |dt|={distance:g}s, "
            f"window={CORRELATION_WINDOW_S:g}s"
        ),
    ), False


def _episodes(events: list[Event]) -> list[list[int]]:
    """Return complete robot episodes from QC approach through go_home."""
    found: list[list[int]] = []
    active: dict[str, list[int]] = {}
    for index, event in enumerate(events):
        mission = event.attrs.get("mission")
        if not event.resource.startswith("robot_") or event.activity not in {"mission_started", "mission_ended"}:
            continue
        if event.activity == "mission_started" and mission == "go_to_qc_bay":
            active.setdefault(event.resource, []).append(index)
            continue
        indexes = active.get(event.resource)
        if indexes is None:
            continue
        indexes.append(index)
        if event.activity == "mission_ended" and mission == "go_home":
            found.append(indexes)
            del active[event.resource]
    return found


def _apply_episodes(events: list[Event], episodes: list[list[int]]) -> list[Event]:
    for indexes in episodes:
        first = next((events[index] for index in indexes if events[index].case_id is not None), None)
        if first is None or first.pallet is None or first.case_id is None:
            continue
        for index in indexes:
            event = events[index]
            if event.case_id is None:
                events[index] = _inferred(
                    event,
                    first,
                    note=(
                        f"{CORRELATION_RULE} v{CASES_VERSION}: episode of {first.resource} "
                        f"from {first.event_id} inherited {first.case_id}"
                    ),
                )
    return events


def assign_cases(events: Iterable[Event]) -> list[Event]:
    """Return events annotated with product cycles and safe QC correlations.

    Case boundaries are observed ``destination_assigned`` events whose stop
    is ``bay5``.  Pallet-bearing events inherit the latest case for that
    pallet.  For a pallet-less QC event or a QC-related robot mission, the
    bay-4 occupancy is preferred.  A complete robot episode from
    ``go_to_qc_bay`` through ``go_home`` inherits the first correlated
    pallet.  The old 60-second assignment window is only a fallback.
    Missing and ambiguous joins remain case-less.
    """
    source = list(events)
    cycles: dict[int, int] = {}
    current: dict[int, str] = {}
    annotated: list[Event] = []

    for event in source:
        updated = event
        if event.pallet is not None:
            if event.activity == "destination_assigned" and event.attrs.get("stop") == "bay5":
                cycle = cycles.get(event.pallet, 0) + 1
                cycles[event.pallet] = cycle
                current[event.pallet] = _case_id(event.pallet, cycle)
            case = current.get(event.pallet)
            if case is not None:
                updated = replace(event, case_id=case)
        annotated.append(updated)

    # Use the already annotated events as correlation anchors.  Keep the
    # latest bay assignment for each case, but retain every case so overlap
    # is detected rather than silently resolved.
    markers: list[Event] = [
        event for event in annotated
        if event.activity == "destination_assigned"
        and str(event.attrs.get("stop", "")).startswith("bay4")
        and event.case_id is not None
        and event.pallet is not None
    ]
    occupancies = _occupancies(annotated)
    correlated: list[Event] = []
    for event in annotated:
        if event.pallet is not None or not _needs_correlation(event):
            correlated.append(event)
            continue
        updated, is_blocked = _correlate_occupancy(event, occupancies)
        if updated.case_id is None and not is_blocked:
            updated, is_blocked = _correlate_fallback(event, markers)
        correlated.append(updated)
    return _apply_episodes(correlated, _episodes(correlated))
