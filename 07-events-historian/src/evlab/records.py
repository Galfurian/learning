"""The contracts: a change (what the collector saw), an event (what a rule made of it), a manifest (where it came from).

Every claim the assistant makes must point at one of these records by id.
"""

import hashlib
import json
from dataclasses import asdict, dataclass, field
from typing import Any

CLAIM_KINDS = ("observed", "derived", "inferred", "confirmed")


@dataclass(frozen=True)
class Manifest:
    """The identity of a recording. Change any field and the cache is a different one."""
    source: str                     # "ice-sim" or "line"
    trace_id: str | None
    trace_version: str | None
    mapping_hash: str               # the logical -> real mapping used
    collector_version: str
    speed: float | None             # replay speed (ice-sim); None on the real line
    clock_basis: str                # "trace-position" or how the line clock was validated

    def key(self) -> str:
        return hashlib.sha256(json.dumps(asdict(self), sort_keys=True).encode()).hexdigest()[:16]

    def to_json(self) -> dict[str, Any]:
        return {"manifest": asdict(self)}


@dataclass(frozen=True)
class Change:
    """One value change of one signal, as the collector received it."""
    change_id: str                  # "c" + sequence
    source: str
    trace_id: str | None
    trace_version: str | None
    machine: str                    # logical machine: "robot_a"
    signal: str                     # logical signal: "robot_a.mission"
    old: Any
    new: Any
    event_time: float | None        # seconds from the start of the trace (ice-sim)
    event_time_lo: float | None     # bounds of event_time: the position polls around the notification
    event_time_hi: float | None
    source_time: str | None         # the server's SourceTimestamp (ice-sim: write time, not event time)
    record_time: str                # collector wall clock, ISO UTC
    clock_quality: str              # "trace-position" on ice-sim
    replay_cycle: int = 0           # the simulator's loop count; not a product cycle
    arrival_seq: int = 0            # the order in which the collector received it (not event-time order)

    def __post_init__(self) -> None:
        lo, hi = self.event_time_lo, self.event_time_hi
        if lo is not None and hi is not None and lo > hi:
            raise ValueError(f"{self.change_id}: event_time_lo {lo} > event_time_hi {hi}")
        if not self.record_time.endswith(("Z", "+00:00")):
            raise ValueError(f"{self.change_id}: record_time must be UTC")
        if self.source == "line" and (self.trace_id or self.trace_version):
            raise ValueError(f"{self.change_id}: a real-line change has no trace id")
        json.dumps([self.old, self.new])   # JSON-safe values or TypeError

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @staticmethod
    def from_json(data: dict[str, Any]) -> "Change":
        return Change(**data)


@dataclass(frozen=True)
class Event:
    """A domain event a rule derived from changes."""
    event_id: str                   # "e" + sequence
    activity: str                   # "mission_started", "check_failed", "destination_assigned", ...
    resource: str                   # logical machine
    event_time: float | None
    event_time_lo: float | None
    event_time_hi: float | None
    evidence: tuple[str, ...]       # change ids
    rule: str
    rule_version: str
    claim_kind: str                 # one of CLAIM_KINDS
    pallet: int | None = None
    case_id: str | None = None      # pallet + product cycle: "p7#2" (cases.py)
    attrs: dict[str, Any] = field(default_factory=dict)   # "mission": "fetch_board_from_storage", "bay": 3, ...
    confidence_note: str = ""       # for inferred claims: the correlation rule and its window

    def __post_init__(self) -> None:
        if self.claim_kind not in CLAIM_KINDS:
            raise ValueError(f"{self.event_id}: claim_kind {self.claim_kind!r} is not one of {CLAIM_KINDS}")
        if self.claim_kind != "observed" and not self.evidence:
            raise ValueError(f"{self.event_id}: a {self.claim_kind} event needs evidence")

    def to_json(self) -> dict[str, Any]:
        data = asdict(self)
        data["evidence"] = list(self.evidence)
        return data

    @staticmethod
    def from_json(data: dict[str, Any]) -> "Event":
        return Event(**{**data, "evidence": tuple(data["evidence"])})


def write_recording(path, manifest: Manifest, changes) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(json.dumps(manifest.to_json()) + "\n")
        for c in changes:
            f.write(json.dumps(c.to_json(), default=str) + "\n")


def read_recording(path) -> tuple[Manifest, list[Change]]:
    with open(path, encoding="utf-8") as f:
        first = json.loads(f.readline())
        manifest = Manifest(**first["manifest"])
        return manifest, [Change.from_json(json.loads(line)) for line in f if line.strip()]
