"""A small, typed SQLite historian for changes and derived events.

The database stores one recording at a time in normal use.  The recording
key is still present on every row so that an in-memory historian can hold
more than one fixture and so that an old cache cannot be mistaken for a new
one.  Query values are parameters, never SQL fragments.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .records import Change, Event, Manifest, read_recording

DEFAULT_LIMIT = 100
MAX_LIMIT = 1_000


class StaleCacheError(ValueError):
    """The database contains a different recording manifest."""


SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS manifest (
    cache_key TEXT PRIMARY KEY,
    source TEXT NOT NULL,
    trace_id TEXT,
    trace_version TEXT,
    mapping_hash TEXT NOT NULL,
    collector_version TEXT NOT NULL,
    speed REAL,
    clock_basis TEXT NOT NULL,
    manifest_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS changes (
    cache_key TEXT NOT NULL REFERENCES manifest(cache_key),
    change_id TEXT NOT NULL,
    source TEXT NOT NULL,
    trace_id TEXT,
    trace_version TEXT,
    machine TEXT NOT NULL,
    signal TEXT NOT NULL,
    old_json TEXT NOT NULL,
    new_json TEXT NOT NULL,
    event_time REAL,
    event_time_lo REAL,
    event_time_hi REAL,
    source_time TEXT,
    record_time TEXT NOT NULL,
    clock_quality TEXT NOT NULL,
    replay_cycle INTEGER NOT NULL,
    arrival_seq INTEGER NOT NULL,
    PRIMARY KEY (cache_key, change_id)
);

CREATE TABLE IF NOT EXISTS events (
    cache_key TEXT NOT NULL REFERENCES manifest(cache_key),
    event_id TEXT NOT NULL,
    activity TEXT NOT NULL,
    resource TEXT NOT NULL,
    event_time REAL,
    event_time_lo REAL,
    event_time_hi REAL,
    rule TEXT NOT NULL,
    rule_version TEXT NOT NULL,
    claim_kind TEXT NOT NULL,
    pallet INTEGER,
    case_id TEXT,
    attrs_json TEXT NOT NULL,
    confidence_note TEXT NOT NULL,
    PRIMARY KEY (cache_key, event_id)
);

CREATE TABLE IF NOT EXISTS event_evidence (
    cache_key TEXT NOT NULL,
    event_id TEXT NOT NULL,
    evidence_seq INTEGER NOT NULL,
    change_id TEXT NOT NULL,
    PRIMARY KEY (cache_key, event_id, evidence_seq),
    UNIQUE (cache_key, event_id, change_id),
    FOREIGN KEY (cache_key, event_id)
        REFERENCES events(cache_key, event_id),
    FOREIGN KEY (cache_key, change_id)
        REFERENCES changes(cache_key, change_id)
);

CREATE INDEX IF NOT EXISTS changes_signal_time
    ON changes (cache_key, signal, event_time);
CREATE INDEX IF NOT EXISTS changes_machine_time
    ON changes (cache_key, machine, event_time);
CREATE INDEX IF NOT EXISTS changes_record_time
    ON changes (cache_key, record_time);
CREATE INDEX IF NOT EXISTS events_activity_time
    ON events (cache_key, activity, event_time);
CREATE INDEX IF NOT EXISTS events_resource_time
    ON events (cache_key, resource, event_time);
CREATE INDEX IF NOT EXISTS events_case_time
    ON events (cache_key, case_id, event_time);
CREATE INDEX IF NOT EXISTS event_evidence_change
    ON event_evidence (cache_key, change_id);
"""


def cache_path(directory: Path, manifest: Manifest) -> Path:
    """Return the SQLite cache path for ``manifest``."""
    return Path(directory) / f"{cache_key(manifest)}.sqlite3"


def cache_key(manifest: Manifest) -> str:
    """The recording's identity plus the versions that derive its events: a new rule or correlation version
    is a new cache, so no event of an older derivation is reused."""
    from .cases import CASES_VERSION
    from .rules import RULES_VERSION
    raw = f"{manifest.key()}|rules={RULES_VERSION}|cases={CASES_VERSION}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _limit(value: int | None) -> int:
    value = DEFAULT_LIMIT if value is None else value
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError("limit must be an integer")
    if value < 1 or value > MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")
    return value


def _time_range(since: float | None, until: float | None) -> tuple[float | None, float | None]:
    for name, value in (("since", since), ("until", until)):
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))):
            raise TypeError(f"{name} must be a number or None")
    if since is not None and until is not None and since > until:
        raise ValueError("since must not be greater than until")
    return since, until


def _text(value: str | None, name: str) -> str | None:
    if value is not None and (not isinstance(value, str) or "\x00" in value):
        raise TypeError(f"{name} must be text or None")
    return value


class Historian:
    """SQLite storage and typed access to one or more logical recordings."""

    def __init__(self, connection: sqlite3.Connection):
        self.db = connection
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript(SCHEMA)

    @classmethod
    def memory(cls) -> "Historian":
        return cls(sqlite3.connect(":memory:"))

    @classmethod
    def open(cls, path: Path, expected: Manifest | None = None) -> "Historian":
        historian = cls(sqlite3.connect(str(path)))
        if expected is not None:
            historian.require_manifest(expected)
        return historian

    @classmethod
    def open_cache(cls, directory: Path, manifest: Manifest) -> "Historian":
        path = cache_path(directory, manifest)
        if not path.exists():
            raise FileNotFoundError(path)
        return cls.open(path, expected=manifest)

    def close(self) -> None:
        self.db.close()

    def __enter__(self) -> "Historian":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _manifest_row(self, key: str) -> sqlite3.Row | None:
        return self.db.execute("SELECT * FROM manifest WHERE cache_key = ?", (key,)).fetchone()

    def _insert_manifest(self, manifest: Manifest) -> str:
        key = cache_key(manifest)
        data = manifest.to_json()["manifest"]
        payload = json.dumps(data, sort_keys=True, separators=(",", ":"))
        row = self._manifest_row(key)
        if row is not None and row["manifest_json"] != payload:
            raise StaleCacheError(f"cache key {key} contains a different manifest")
        self.db.execute(
            """INSERT OR IGNORE INTO manifest
               (cache_key, source, trace_id, trace_version, mapping_hash,
                collector_version, speed, clock_basis, manifest_json)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (key, manifest.source, manifest.trace_id, manifest.trace_version,
             manifest.mapping_hash, manifest.collector_version, manifest.speed,
             manifest.clock_basis, payload),
        )
        return key

    def require_manifest(self, expected: Manifest) -> str:
        key = cache_key(expected)
        row = self._manifest_row(key)
        if row is None:
            found = self.db.execute("SELECT cache_key FROM manifest LIMIT 1").fetchone()
            if found is not None:
                raise StaleCacheError(
                    f"expected cache {key}, found {found['cache_key']}"
                )
            raise ValueError(f"recording manifest {key} is not loaded")
        if row["manifest_json"] != json.dumps(
            expected.to_json()["manifest"], sort_keys=True, separators=(",", ":")
        ):
            raise StaleCacheError(f"cache key {key} contains a different manifest")
        return key

    def manifest(self, manifest: Manifest | str | None = None) -> Manifest | None:
        """Return a loaded manifest, optionally selected by object or key."""
        if isinstance(manifest, Manifest):
            key = cache_key(manifest)
        else:
            key = manifest
        if key is None:
            row = self.db.execute("SELECT * FROM manifest ORDER BY cache_key LIMIT 1").fetchone()
        else:
            row = self._manifest_row(key)
        if row is None:
            return None
        return Manifest(
            row["source"], row["trace_id"], row["trace_version"],
            row["mapping_hash"], row["collector_version"], row["speed"],
            row["clock_basis"],
        )

    def load(self, manifest: Manifest, changes: Iterable[Change]) -> str:
        """Load a manifest and changes. Repeating the load is idempotent."""
        key = cache_key(manifest)
        with self.db:
            self._insert_manifest(manifest)
            for change in changes:
                self._insert_change(key, change)
        return key

    def load_recording(self, path: Path) -> str:
        manifest, changes = read_recording(path)
        return self.load(manifest, changes)

    def _insert_change(self, key: str, change: Change) -> None:
        values = (
            key, change.change_id, change.source, change.trace_id,
            change.trace_version, change.machine, change.signal,
            json.dumps(change.old, sort_keys=True, separators=(",", ":")),
            json.dumps(change.new, sort_keys=True, separators=(",", ":")),
            change.event_time, change.event_time_lo, change.event_time_hi,
            change.source_time, change.record_time, change.clock_quality,
            change.replay_cycle, change.arrival_seq,
        )
        existing = self.db.execute(
            "SELECT * FROM changes WHERE cache_key = ? AND change_id = ?",
            (key, change.change_id),
        ).fetchone()
        if existing is not None:
            if self._change_from_row(existing) != change:
                raise ValueError(f"change {change.change_id} differs from the loaded recording")
            return
        self.db.execute(
            """INSERT INTO changes
            (cache_key, change_id, source, trace_id, trace_version, machine,
             signal, old_json, new_json, event_time, event_time_lo,
             event_time_hi, source_time, record_time, clock_quality,
             replay_cycle, arrival_seq)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            values,
        )

    def add_events(self, manifest: Manifest | str, events: Iterable[Event]) -> None:
        """Store events and their change evidence for a loaded recording."""
        key = cache_key(manifest) if isinstance(manifest, Manifest) else manifest
        if not isinstance(key, str) or self._manifest_row(key) is None:
            raise ValueError(f"recording manifest {key!r} is not loaded")
        with self.db:
            for event in events:
                self._insert_event(key, event)

    def _insert_event(self, key: str, event: Event) -> None:
        for change_id in event.evidence:
            if self.db.execute(
                "SELECT 1 FROM changes WHERE cache_key = ? AND change_id = ?",
                (key, change_id),
            ).fetchone() is None:
                raise ValueError(f"event {event.event_id} cites unknown change {change_id}")
        attrs = json.dumps(event.attrs, sort_keys=True, separators=(",", ":"))
        existing = self.db.execute(
            "SELECT * FROM events WHERE cache_key = ? AND event_id = ?",
            (key, event.event_id),
        ).fetchone()
        if existing is not None:
            if self._event_from_row(existing, self.evidence(key, event.event_id)) != event:
                raise ValueError(f"event {event.event_id} differs from the loaded recording")
            return
        self.db.execute(
            """INSERT INTO events
            (cache_key, event_id, activity, resource, event_time,
             event_time_lo, event_time_hi, rule, rule_version, claim_kind,
             pallet, case_id, attrs_json, confidence_note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (key, event.event_id, event.activity, event.resource, event.event_time,
             event.event_time_lo, event.event_time_hi, event.rule,
             event.rule_version, event.claim_kind, event.pallet, event.case_id,
             attrs, event.confidence_note),
        )
        self.db.executemany(
            """INSERT INTO event_evidence
               (cache_key, event_id, evidence_seq, change_id)
               VALUES (?, ?, ?, ?)""",
            [(key, event.event_id, sequence, change_id)
             for sequence, change_id in enumerate(event.evidence)],
        )

    def evidence(self, cache_key_value: str, event_id: str) -> list[str]:
        rows = self.db.execute(
            """SELECT change_id FROM event_evidence
               WHERE cache_key = ? AND event_id = ? ORDER BY evidence_seq""",
            (cache_key_value, event_id),
        ).fetchall()
        return [row["change_id"] for row in rows]

    @staticmethod
    def _change_from_row(row: sqlite3.Row) -> Change:
        return Change(
            row["change_id"], row["source"], row["trace_id"], row["trace_version"],
            row["machine"], row["signal"], json.loads(row["old_json"]),
            json.loads(row["new_json"]), row["event_time"], row["event_time_lo"],
            row["event_time_hi"], row["source_time"], row["record_time"],
            row["clock_quality"], row["replay_cycle"], row["arrival_seq"],
        )

    @staticmethod
    def _event_from_row(row: sqlite3.Row, evidence: Iterable[str]) -> Event:
        return Event(
            row["event_id"], row["activity"], row["resource"], row["event_time"],
            row["event_time_lo"], row["event_time_hi"], tuple(evidence),
            row["rule"], row["rule_version"], row["claim_kind"], row["pallet"],
            row["case_id"], json.loads(row["attrs_json"]), row["confidence_note"],
        )

    def changes(
        self,
        *,
        machine: str | None = None,
        path_like: str | None = None,
        since: float | None = None,
        until: float | None = None,
        limit: int | None = None,
        recording_key: str | None = None,
    ) -> list[Change]:
        """Query changes; ``since`` is inclusive and ``until`` is exclusive."""
        machine = _text(machine, "machine")
        path_like = _text(path_like, "path_like")
        recording_key = _text(recording_key, "recording_key")
        since, until = _time_range(since, until)
        params: list[Any] = []
        where: list[str] = []
        if recording_key is not None:
            where.append("cache_key = ?")
            params.append(recording_key)
        if machine is not None:
            where.append("machine = ?")
            params.append(machine)
        if path_like is not None:
            where.append("signal LIKE ?")
            params.append(path_like)
        if since is not None:
            where.append("event_time >= ?")
            params.append(since)
        if until is not None:
            where.append("event_time < ?")
            params.append(until)
        query = "SELECT * FROM changes"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY event_time_lo IS NULL, event_time_lo, arrival_seq, change_id LIMIT ?"
        params.append(_limit(limit))
        return [self._change_from_row(row) for row in self.db.execute(query, params)]

    def events(
        self,
        *,
        activity: str | None = None,
        resource: str | None = None,
        pallet: int | None = None,
        case_id: str | None = None,
        since: float | None = None,
        until: float | None = None,
        limit: int | None = None,
        recording_key: str | None = None,
    ) -> list[Event]:
        """Query events; ``since`` is inclusive and ``until`` is exclusive."""
        activity = _text(activity, "activity")
        resource = _text(resource, "resource")
        case_id = _text(case_id, "case_id")
        recording_key = _text(recording_key, "recording_key")
        if pallet is not None and (isinstance(pallet, bool) or not isinstance(pallet, int)):
            raise TypeError("pallet must be an integer or None")
        since, until = _time_range(since, until)
        params: list[Any] = []
        where: list[str] = []
        if recording_key is not None:
            where.append("cache_key = ?")
            params.append(recording_key)
        if activity is not None:
            where.append("activity = ?")
            params.append(activity)
        if resource is not None:
            where.append("resource = ?")
            params.append(resource)
        if pallet is not None:
            where.append("pallet = ?")
            params.append(pallet)
        if case_id is not None:
            where.append("case_id = ?")
            params.append(case_id)
        if since is not None:
            where.append("event_time >= ?")
            params.append(since)
        if until is not None:
            where.append("event_time < ?")
            params.append(until)
        query = "SELECT * FROM events"
        if where:
            query += " WHERE " + " AND ".join(where)
        query += " ORDER BY event_time_lo IS NULL, event_time_lo, event_id LIMIT ?"
        params.append(_limit(limit))
        rows = self.db.execute(query, params).fetchall()
        return [self._event_from_row(row, self.evidence(row["cache_key"], row["event_id"])) for row in rows]

