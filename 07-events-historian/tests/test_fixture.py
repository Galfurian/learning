import importlib.util
import re
from pathlib import Path

from evlab.mapping import EXAMPLE_MAPPING, load_mapping
from evlab.records import read_recording

BUILD_PATH = Path(__file__).parents[1] / "data" / "fixture" / "build.py"
SPEC = importlib.util.spec_from_file_location("fixture_build", BUILD_PATH)
assert SPEC and SPEC.loader
BUILD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(BUILD)
RECORDING = BUILD.RECORDING
build = BUILD.build


def test_fixture_is_deterministic_and_uses_logical_names():
    manifest, changes, labels = build()
    saved_manifest, saved_changes = read_recording(RECORDING)
    assert manifest == saved_manifest
    assert changes == saved_changes
    assert manifest.trace_id == "fixture"
    assert manifest.source == "ice-sim"
    assert all(re.fullmatch(r"c\d+", change.change_id) for change in changes)
    assert all("ns=" not in change.signal and "opc" not in change.signal.lower() for change in changes)


def test_fixture_has_all_negative_cases():
    _, changes, labels = build()
    ids = {change.change_id for change in changes}
    required = {
        "first_value", "duplicate", "unchanged", "out_of_order", "assignment_only",
        "missing_correlation", "pallet_7_rework_missions", "pallet_7_cycle_2",
    }
    assert required <= set(labels)
    assert all(change_id in ids for group in labels.values() for change_id in group)
    assert len(labels["duplicate"]) == 2
    assert len(labels["missing_correlation"]) == 3
    assert changes[0].old is None
    out_of_order = [changes[int(change_id[1:]) - 1] for change_id in labels["out_of_order"]]
    assert out_of_order[0].arrival_seq < out_of_order[1].arrival_seq
    assert out_of_order[0].event_time > out_of_order[1].event_time
    assert out_of_order[0].event_time_lo == out_of_order[1].event_time_lo
    assert out_of_order[0].event_time_hi == out_of_order[1].event_time_hi


def test_fixture_signals_exist_in_example_mapping():
    mapping, _ = load_mapping(EXAMPLE_MAPPING)
    _, changes, _ = build()
    assert {change.signal for change in changes} <= set(mapping.signals)

