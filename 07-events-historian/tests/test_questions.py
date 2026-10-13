import importlib.util
import json
import re
import subprocess
from pathlib import Path

from evlab.cases import CASES_VERSION
from evlab.records import read_recording
from evlab.recordings import resolve
from evlab.rules import clean, derive
from evlab.cases import assign_cases

ROOT = Path(__file__).parents[1]
FORBIDDEN = re.compile(r"(?:ns=|opc\.tcp|https?://|\b(?:token|password|secret)\b|\b\d{1,3}(?:\.\d{1,3}){3}\b)", re.I)


def load_questions(name: str) -> dict:
    return json.loads((ROOT / "data" / name).read_text(encoding="utf-8"))


def test_question_files_have_one_contract_and_no_real_identifiers():
    seen = set()
    aliases = {"lab-session", "lab-demo", "holdout", "fixture"}
    for name in ("dev.json", "holdout.json"):
        data = load_questions(name)
        assert data["case_version"] == CASES_VERSION
        assert data["correlation_version"] == CASES_VERSION
        assert data["questions"]
        assert data["recording"] in aliases
        for question in data["questions"]:
            assert question["recording"] in aliases
            assert question["id"] not in seen
            seen.add(question["id"])
            assert question["type"] in {"what-happened", "why", "why-no-rule", "where", "when", "who", "coverage", "abstain"}
            assert isinstance(question["gold_event_ids"], list)
            assert isinstance(question["gold_activities"], list)
            assert isinstance(question["gold_answer"], str) and question["gold_answer"]
            expect = question["expect"]
            assert set(expect) == {"all", "none"}
            for kind in ("all", "none"):
                assert all(isinstance(group, list) and group for group in expect[kind])
                assert all(all(isinstance(term, str) and term for term in group) for group in expect[kind])
            answer = question["gold_answer"].casefold()
            assert all(any(term.casefold() in answer for term in group) for group in expect["all"])
            assert not FORBIDDEN.search(question["text"])


def test_fixture_gold_events_and_activities_exist():
    spec = importlib.util.spec_from_file_location("fixture_build", ROOT / "data" / "fixture" / "build.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _, changes, _ = module.build()
    kept, _ = clean(changes)
    events = assign_cases(derive(kept))
    ids = {event.event_id for event in events}
    activities = {event.activity for event in events}
    for question in load_questions("dev.json")["questions"]:
        if question["recording"] != "fixture":
            assert question["needs_recording"] is True
            continue
        assert question["needs_recording"] is False
        assert set(question["gold_event_ids"]) <= ids
        assert set(question["gold_activities"]) <= activities


def test_holdout_transform_is_deterministic_when_the_local_source_exists():
    path = resolve("lab-session")
    if not path.exists():
        return
    spec = importlib.util.spec_from_file_location("holdout_build", ROOT / "data" / "holdout" / "build.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _manifest, changes = module.transform(*read_recording(path))
    assert len(changes) == 2276
    assert all("ns=" not in change.signal and "opc" not in change.signal.lower() for change in changes)

    kept, _ = clean(changes)
    events = assign_cases(derive(kept))
    ids = {event.event_id for event in events}
    activities = {event.activity for event in events}
    for question in load_questions("holdout.json")["questions"]:
        assert set(question["gold_event_ids"]) <= ids
        assert set(question["gold_activities"]) <= activities


def test_tracked_files_contain_no_local_trace_ids_or_manifest_keys():
    tracked = subprocess.check_output(
        ["git", "ls-files", "07-events-historian"],
        cwd=ROOT.parent,
        text=True,
    ).splitlines()
    trace_map = ROOT / ".local" / "traces.json"
    if trace_map.exists():
        traces = json.loads(trace_map.read_text(encoding="utf-8"))
        real_trace_ids = {
            item["trace"] for item in traces.values()
            if isinstance(item, dict) and isinstance(item.get("trace"), str)
        }
        for relative in tracked:
            text = (ROOT.parent / relative).read_text(encoding="utf-8", errors="replace")
            assert not any(trace_id in text for trace_id in real_trace_ids), relative

    for relative in tracked:
        path = ROOT.parent / relative
        if path.suffix == ".json" and "data" in path.parts:
            text = path.read_text(encoding="utf-8")
            assert not re.search(r"\b[0-9a-f]{16}\b", text, re.I), relative
