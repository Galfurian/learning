"""Build the deterministic, offline holdout recording.

The source is a local cached recording.  This script does not contact the
simulator and writes the derived recording only below ``.cache/``.  The
changes are transformed before cleaning and event derivation so the holdout
tests the pipeline, not a copied event table.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from evlab.records import Change, Manifest, read_recording, write_recording
from evlab.recordings import recording_path, resolve

UNIT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ALIAS = "lab-session"
BASE_TIME = datetime(2026, 10, 13, tzinfo=timezone.utc)
VERSION = "holdout-transform-v1"
PALLETS = {7: 17, 8: 18, 9: 19}
ROBOT_SWAP = {"robot_a": "robot_b", "robot_b": "robot_a"}


def _remap_pallet(value, signal: str):
    if not (signal.startswith("conveyor.destination") or signal.startswith("conveyor.segment")):
        return value
    if isinstance(value, bool):
        return value
    return PALLETS.get(value, value)


def _machine_signal(machine: str, signal: str) -> tuple[str, str]:
    if machine not in ROBOT_SWAP:
        return machine, signal
    return ROBOT_SWAP[machine], signal.replace(f"{machine}.", f"{ROBOT_SWAP[machine]}.", 1)


def _extra(machine: str, signal: str, old, new, event_time: float) -> Change:
    return Change(
        "extra", "offline-transform", "holdout", VERSION, machine, signal, old, new,
        event_time, event_time - 0.1, event_time + 0.1, None, BASE_TIME.isoformat().replace("+00:00", "Z"),
        "trace-position", 0, 0,
    )


def transform(source_manifest: Manifest, source: list[Change]) -> tuple[Manifest, list[Change]]:
    """Apply v1 mutations to raw changes and return a new manifest and rows."""
    rows: list[Change] = []
    for change in sorted(source, key=lambda item: item.arrival_seq):
        machine, signal = _machine_signal(change.machine, change.signal)
        rows.append(Change(
            "pending", "offline-transform", "holdout", VERSION, machine, signal,
            _remap_pallet(change.old, signal), _remap_pallet(change.new, signal),
            change.event_time, change.event_time_lo, change.event_time_hi, None,
            BASE_TIME.isoformat().replace("+00:00", "Z"), "trace-position", change.replay_cycle, 0,
        ))

    # Make pallet 18 fail its QC check.  The extra False transition is after
    # the original True result, so clean() keeps it as a real change.
    rows.append(_extra("qc_station", "qc_station.last_result", True, False, 708.557))

    # Copy the p7 robot episode to a later time.  After the global robot swap
    # it is robot_a, and the case correlation must still find pallet 18.
    p7_missions = [
        change for change in source
        if change.machine == "robot_b" and change.signal == "robot_b.mission"
        and 404.0 <= (change.event_time or -1) <= 614.0
    ]
    for change in p7_missions:
        shifted = (change.event_time or 0.0) + 326.0
        machine, signal = _machine_signal("robot_b", "robot_b.mission")
        rows.append(_extra(machine, signal, change.old, change.new, shifted))

    # A p9 check with no result signal, outside every QC-bay occupancy.
    rows.extend([
        _extra("qc_station", "qc_station.mission", None, "", 650.0),
        _extra("qc_station", "qc_station.mission", "", "check_object", 651.0),
        _extra("qc_station", "qc_station.mission", "check_object", "", 652.0),
    ])

    # A destination assignment for p9 without a matching FIFO movement.
    rows.extend([
        _extra("conveyor", "conveyor.destination.bay1_1", None, 0, 660.0),
        _extra("conveyor", "conveyor.destination.bay1_1", 0, PALLETS[9], 661.0),
    ])

    normalized: list[Change] = []
    for sequence, change in enumerate(rows, start=1):
        normalized.append(Change(
            f"c{sequence}", change.source, change.trace_id, change.trace_version,
            change.machine, change.signal, change.old, change.new, change.event_time,
            change.event_time_lo, change.event_time_hi, change.source_time,
            (BASE_TIME + timedelta(seconds=sequence)).isoformat().replace("+00:00", "Z"),
            change.clock_quality, change.replay_cycle, sequence,
        ))
    if not source:
        raise ValueError("the source recording is empty")
    manifest = Manifest(
        "offline-transform", "holdout", VERSION, source_manifest.mapping_hash,
        "offline-transform-1", 1.0, "trace-position",
    )
    return manifest, normalized


def output_path(manifest: Manifest) -> Path:
    return recording_path("holdout", manifest)


def build() -> tuple[Manifest, list[Change], Path]:
    source = resolve(SOURCE_ALIAS)
    if not source.exists():
        raise FileNotFoundError(f"missing local source recording for alias {SOURCE_ALIAS!r}: {source}")
    source_manifest, source_changes = read_recording(source)
    manifest, changes = transform(source_manifest, source_changes)
    path = output_path(manifest)
    write_recording(path, manifest, changes)
    return manifest, changes, path


if __name__ == "__main__":
    manifest, changes, path = build()
    print(f"wrote {path} ({len(changes)} changes, key {manifest.key()})")
