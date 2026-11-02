"""The event log after abstraction: one entry per operation start or complete."""

from collections import Counter, defaultdict
from dataclasses import dataclass

from pmlab.rules import number


@dataclass(frozen=True)
class Entry:
    case_id: str
    activity: str
    lifecycle: str                  # "start" | "complete"
    time: float
    resource: str
    objects: tuple[str, ...]        # "order:3", "pallet:7", "robot_b"
    source_ids: tuple[str, ...]
    claim_kind: str


@dataclass
class Trace:
    case_id: str
    entries: list[Entry]

    @property
    def activities(self) -> tuple[str, ...]:
        """Activities of the complete entries, in order."""
        return tuple(e.activity for e in self.entries if e.lifecycle == "complete")


def sort_key(entry: Entry) -> tuple[float, int]:
    return entry.time, number(entry.source_ids[0])


def to_log(entries: list[Entry], case_notion: str = "order") -> list[Trace]:
    """Group entries into traces by case notion: "order" or "pallet".

    Under "pallet" an entry goes to every pallet in its objects, so an entry
    with two pallets appears in two traces (divergence). Entries sort by
    (time, number of the first source id). Traces sort by case id.
    """
    if case_notion not in ("order", "pallet"):
        raise ValueError(f"unknown case notion: {case_notion}")
    groups: dict[str, list[Entry]] = defaultdict(list)
    for entry in entries:
        if case_notion == "order":
            groups[entry.case_id].append(entry)
        else:
            for obj in entry.objects:
                if obj.startswith("pallet:"):
                    groups[obj].append(entry)
    return [Trace(c, sorted(es, key=sort_key)) for c, es in sorted(groups.items(), key=lambda kv: (len(kv[0]), kv[0]))]


def variants(traces: list[Trace]) -> Counter[tuple[str, ...]]:
    """Count the distinct activity sequences (complete entries)."""
    return Counter(t.activities for t in traces)
