"""Build the small offline recording used by unit 07.

The fixture uses logical names from ``data/mapping.example.json``.  Its rows
stay in collector arrival order, while their event-time bounds contain the
duplicate, unchanged, and out-of-order cases used by the exercises.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from evlab.mapping import EXAMPLE_MAPPING, load_mapping
from evlab.records import Change, Manifest, write_recording

FIXTURE_DIR = Path(__file__).resolve().parent
RECORDING = FIXTURE_DIR / "recording.jsonl"
BASE_TIME = datetime(2026, 10, 13, 10, 0, tzinfo=timezone.utc)


def build() -> tuple[Manifest, list[Change], dict[str, tuple[str, ...]]]:
    mapping, _ = load_mapping(EXAMPLE_MAPPING)
    manifest = Manifest(
        source="ice-sim",
        trace_id="fixture",
        trace_version="fixture-v1",
        mapping_hash=mapping.hash(),
        collector_version="fixture-1",
        speed=1.0,
        clock_basis="trace-position",
    )
    rows: list[Change] = []
    labels: defaultdict[str, list[str]] = defaultdict(list)

    def add(
        label: str,
        machine: str,
        signal: str,
        old: Any,
        new: Any,
        event_time: float,
        *,
        lo: float | None = None,
        hi: float | None = None,
    ) -> None:
        number = len(rows) + 1
        if lo is None:
            lo = event_time - 0.1
        if hi is None:
            hi = event_time + 0.1
        rows.append(Change(
            change_id=f"c{number}",
            source="ice-sim",
            trace_id="fixture",
            trace_version="fixture-v1",
            machine=machine,
            signal=signal,
            old=old,
            new=new,
            event_time=event_time,
            event_time_lo=lo,
            event_time_hi=hi,
            source_time=None,
            record_time=(BASE_TIME + timedelta(seconds=number)).isoformat().replace("+00:00", "Z"),
            clock_quality="trace-position",
            replay_cycle=0,
            arrival_seq=number,
        ))
        labels[label].append(f"c{number}")

    # Product cycle 1: pallet 7 fails QC and is sent to the rework bin.
    add("first_value", "conveyor", "conveyor.destination.bay5", None, 0, 3.0)
    add("pallet_7_loaded", "conveyor", "conveyor.destination.bay5", 0, 7, 4.0)
    add("pallet_7_loaded", "conveyor", "conveyor.segment1.item0", 0, 7, 5.0)
    add("first_value", "conveyor", "conveyor.destination.bay4_1", None, 0, 7.0)
    add("pallet_7_route", "conveyor", "conveyor.destination.bay4_1", 0, 7, 8.0)
    add("pallet_7_route_ok", "conveyor", "conveyor.destination_ok.bay4_2", False, True, 8.2)
    add("first_value", "qc_station", "qc_station.mission", None, "", 19.0)
    add("first_value", "qc_station", "qc_station.last_result", None, True, 19.0)
    add("pallet_7_check", "qc_station", "qc_station.mission", "", "check_object", 20.0)
    add("pallet_7_failed", "qc_station", "qc_station.last_result", True, False, 21.0)
    add("pallet_7_check_end", "qc_station", "qc_station.mission", "check_object", "", 22.0)
    add("first_value", "robot_b", "robot_b.mission", None, "", 27.0)
    add("pallet_7_rework_missions", "robot_b", "robot_b.mission", "", "go_to_qc_bay", 28.0)
    add("pallet_7_rework_missions", "robot_b", "robot_b.mission", "go_to_qc_bay", "", 29.0)
    add("pallet_7_rework_missions", "robot_b", "robot_b.mission", "", "take_cover_top_from_pallet", 30.0)
    add("pallet_7_rework_missions", "robot_b", "robot_b.mission", "take_cover_top_from_pallet", "", 31.0)
    add("pallet_7_rework_missions", "robot_b", "robot_b.mission", "", "take_cover_bottom_from_pallet", 32.0)
    add("pallet_7_rework_missions", "robot_b", "robot_b.mission", "take_cover_bottom_from_pallet", "", 33.0)
    add("pallet_7_rework_missions", "robot_b", "robot_b.mission", "", "go_to_bin", 90.0)
    add("pallet_7_rework_missions", "robot_b", "robot_b.mission", "go_to_bin", "", 91.0)
    add("pallet_7_rework_missions", "robot_b", "robot_b.mission", "", "drop_covers_in_bin", 92.0)
    add("pallet_7_rework_missions", "robot_b", "robot_b.mission", "drop_covers_in_bin", "", 93.0)
    add("pallet_7_rework_missions", "robot_b", "robot_b.mission", "", "go_home", 94.0)
    add("pallet_7_rework_missions", "robot_b", "robot_b.mission", "go_home", "", 95.0)
    add("pallet_7_left_bay", "conveyor", "conveyor.destination.bay4_1", 7, 0, 34.2)

    # Product cycle 1: pallet 8 passes the same check.
    add("pallet_8_loaded", "conveyor", "conveyor.destination.bay5", 7, 8, 120.0)
    add("pallet_8_loaded", "conveyor", "conveyor.segment1.item1", 0, 8, 121.0)
    add("pallet_8_route", "conveyor", "conveyor.destination.bay4_1", 0, 8, 124.0)
    add("pallet_8_check", "qc_station", "qc_station.mission", "", "check_object", 135.0)
    add("pallet_8_passed", "qc_station", "qc_station.last_result", False, True, 136.0)
    add("pallet_8_check_end", "qc_station", "qc_station.mission", "check_object", "", 137.0)

    # Assignment without movement: this must not become a "went to bay" claim.
    add("first_value", "conveyor", "conveyor.destination.bay3_1", None, 0, 139.0)
    add("assignment_only", "conveyor", "conveyor.destination.bay3_1", 0, 9, 140.0)

    # Product cycle 2 reuses pallet id 7. The loading event creates p7#2.
    add("pallet_7_cycle_2", "conveyor", "conveyor.destination.bay5", 8, 7, 180.0)
    add("pallet_7_cycle_2", "conveyor", "conveyor.segment1.item0", 7, 0, 180.5)
    add("pallet_7_cycle_2", "conveyor", "conveyor.segment1.item0", 0, 7, 181.0)
    add("pallet_7_cycle_2", "conveyor", "conveyor.destination.bay4_1", 8, 7, 184.0)

    # Two product cases occupy bay 4 at once.  A QC-related mission must
    # remain unassigned instead of choosing the closest pallet.
    add("ambiguous_bay4", "robot_a", "robot_a.mission", None, "", 199.0)
    add("ambiguous_bay4", "robot_a", "robot_a.mission", "", "go_to_qc_bay", 200.0)
    add("ambiguous_bay4", "robot_a", "robot_a.mission", "go_to_qc_bay", "", 201.0)

    # The next two notifications arrive in this order, but their event-time
    # intervals overlap and their nominal times are reversed.
    add("out_of_order", "robot_a", "robot_a.mission_count", 1, 2, 220.0, lo=219.5, hi=220.5)
    add("out_of_order", "robot_a", "robot_a.busy", False, True, 219.8, lo=219.5, hi=220.5)

    # A duplicate notification and an unchanged value are raw collector rows.
    add("duplicate", "mill_cell", "mill_cell.alarm_message", "", "vice_open", 240.0)
    add("duplicate", "mill_cell", "mill_cell.alarm_message", "", "vice_open", 240.0)
    add("unchanged", "qc_station", "qc_station.busy", False, False, 241.0)

    # A check with no nearby pallet is deliberately uncorrelated.
    add("missing_correlation", "qc_station", "qc_station.mission", "", "check_object", 300.0)
    add("missing_correlation", "qc_station", "qc_station.last_result", True, False, 301.0)
    add("missing_correlation", "qc_station", "qc_station.mission", "check_object", "", 302.0)

    return manifest, rows, {name: tuple(ids) for name, ids in labels.items()}


def main() -> None:
    manifest, changes, _ = build()
    RECORDING.parent.mkdir(parents=True, exist_ok=True)
    write_recording(RECORDING, manifest, changes)
    print(f"wrote {RECORDING} ({len(changes)} changes, key {manifest.key()})")


if __name__ == "__main__":
    main()

