"""Low-level events in the unit 07 export shape, read and written as JSONL.

The first line of a file is the header, for example
{"log": "train", "injected": [...]}. Every other line is one event.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Event:
    event_id: str
    activity: str
    resource: str
    time: float
    pallet: int | None
    claim_kind: str
    attrs: dict[str, Any]
    evidence: tuple[str, ...]


def read_events(path: Path) -> tuple[dict, list[Event]]:
    lines = [line for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]
    header = json.loads(lines[0]) if lines else {}
    events = []
    for line in lines[1:]:
        row = json.loads(line)
        events.append(Event(
            event_id=row["event_id"],
            activity=row["activity"],
            resource=row["resource"],
            time=float(row["event_time"]),
            pallet=row.get("pallet"),
            claim_kind=row["claim_kind"],
            attrs=row.get("attrs", {}),
            evidence=tuple(row.get("evidence", ())),
        ))
    return header, events


def write_events(path: Path, header: dict, events: list[Event]) -> None:
    rows = [json.dumps(header, sort_keys=True)]
    for event in events:
        rows.append(json.dumps({
            "event_id": event.event_id,
            "activity": event.activity,
            "resource": event.resource,
            "event_time": event.time,
            "pallet": event.pallet,
            "claim_kind": event.claim_kind,
            "attrs": event.attrs,
            "evidence": list(event.evidence),
        }, sort_keys=True))
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")
