"""Shared test helpers: committed logs to entries, and the pm4py bridge."""

import json
from collections import Counter
from functools import cache

from pmlab.abstraction import abstract
from pmlab.events import read_events
from pmlab.log import Entry
from pmlab.orders import correlate
from pmlab.recipes import UNIT_ROOT, load_recipes
from pmlab.reference import to_pm4py_log  # noqa: F401  (re-export for the tests)
from pmlab.rules import derive_extra


@cache
def _entries(name: str) -> tuple[Entry, ...]:
    for folder in ("logs", "orders"):
        path = UNIT_ROOT / "data" / folder / f"{name}.jsonl"
        if path.exists():
            break
    _, events = read_events(path)
    events = derive_extra(events)
    orders = correlate(events, load_recipes())
    return tuple(abstract(events, load_recipes(), orders))


def entries_of(name: str) -> list[Entry]:
    """Entries of a committed log (`train`, `ref-order`, ...), cached."""
    return list(_entries(name))


def truth_order(trace, owner: dict[str, str]) -> str:
    """Truth order of a trace: the order that owns most of its source event ids."""
    votes = Counter(owner[s] for e in trace.entries for s in e.source_ids if s in owner)
    return votes.most_common(1)[0][0]


def truth_of(name: str = "train") -> dict:
    """The `orders` part of a committed truth file."""
    return json.loads((UNIT_ROOT / "data" / "logs" / f"{name}.truth.json").read_text(encoding="utf-8"))["orders"]
