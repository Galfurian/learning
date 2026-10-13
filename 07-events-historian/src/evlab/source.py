"""Which recording an exercise reads: a cached ice-sim recording, or the invented fixture.

No exercise needs the tailnet: the first run with ICE_SIM_URL records into
.cache/ (scripts/record.py); without a cache the exercises use the fixture and
say so.
"""

from dataclasses import dataclass

from .records import Change, Manifest, read_recording
from .recordings import FIXTURE, find

DEFAULT_TRACE = "lab-session"   # a logical alias (recordings.py)


@dataclass
class Source:
    label: str
    manifest: Manifest
    changes: list[Change]


def load(trace: str = DEFAULT_TRACE, *, speed: float | None = 1.0, fixture: bool = False) -> Source:
    path = None if fixture else find(trace, speed)
    if path is None:
        manifest, changes = read_recording(FIXTURE)
        why = "--fixture" if fixture else f"no cached recording of {trace} at speed {speed}"
        return Source(f"the invented fixture ({why})", manifest, changes)
    manifest, changes = read_recording(path)
    return Source(f"{trace} recorded at speed {manifest.speed:g}", manifest, changes)
