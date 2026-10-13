"""Where recordings live: .cache/recordings/<alias>-<manifest key>.jsonl (git-ignored).

Tracked files name a recording only by a logical alias ("lab-session",
"holdout", "fixture"). The alias -> real trace id map lives in the
git-ignored .local/traces.json: {"lab-session": {"trace": "<real trace id>"}}.
"""

import json
from pathlib import Path

from .mapping import UNIT_ROOT
from .records import Manifest, read_recording

RECORDINGS = UNIT_ROOT / ".cache" / "recordings"
FIXTURE = UNIT_ROOT / "data" / "fixture" / "recording.jsonl"
TRACES = UNIT_ROOT / ".local" / "traces.json"


def real_trace(alias: str) -> str:
    """The simulator's trace id of a logical alias (lab members only)."""
    if not TRACES.exists():
        raise FileNotFoundError(f"no {TRACES}: write {{\"{alias}\": {{\"trace\": \"<trace id>\"}}}} there first")
    table = json.loads(TRACES.read_text(encoding="utf-8"))
    if alias not in table:
        raise KeyError(f"alias {alias!r} is not in {TRACES}")
    return table[alias]["trace"]


def recording_path(alias: str, manifest: Manifest) -> Path:
    RECORDINGS.mkdir(parents=True, exist_ok=True)
    return RECORDINGS / f"{alias}-{manifest.key()}.jsonl"


def find(alias: str, speed: float | None = None) -> Path | None:
    """The newest cached recording of an alias (at a speed, if given); None if there is none."""
    hits = []
    for path in RECORDINGS.glob(f"{alias}-*.jsonl"):
        manifest, _ = read_recording(path)
        if speed is None or manifest.speed == speed:
            hits.append(path)
    return max(hits, key=lambda p: p.stat().st_mtime) if hits else None


def resolve(alias: str, speed: float | None = 1.0) -> Path:
    """The recording of an alias, or an error that says how to make it."""
    if alias == "fixture":
        return FIXTURE
    path = find(alias, speed)
    if path is None:
        raise FileNotFoundError(f"no cached recording '{alias}' at speed {speed}: run scripts/record.py "
                                f"(or data/holdout/build.py for 'holdout')")
    return path
