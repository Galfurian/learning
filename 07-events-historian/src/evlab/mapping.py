"""Logical names <-> the line's real node ids and values.

The repository knows only logical names ("robot_a.mission"). The real node ids
and the real values live in a local, git-ignored file (.local/mapping.json),
built from the simulator's catalog by scripts/build_mapping.py. The
invented fixture uses data/mapping.example.json.

{"machines": {"robot_a": {"server": "<real server name>", "signals": {"mission": "<node id>", ...}}},
 "values":   {"robot_a.mission": {"<real value>": "fetch_board_from_storage", ...}}}
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

UNIT_ROOT = Path(__file__).resolve().parents[2]
LOCAL_MAPPING = UNIT_ROOT / ".local" / "mapping.json"
EXAMPLE_MAPPING = UNIT_ROOT / "data" / "mapping.example.json"


@dataclass(frozen=True)
class Signal:
    name: str           # "robot_a.mission"
    machine: str        # "robot_a"
    node_id: str        # the real node id (local mapping) or a placeholder (example)


class Mapping:
    def __init__(self, data: dict[str, Any]) -> None:
        self.data = data
        self.signals: dict[str, Signal] = {}
        self.by_node: dict[tuple[str, str], Signal] = {}
        for machine, spec in data.get("machines", {}).items():
            for short, node_id in spec.get("signals", {}).items():
                sig = Signal(f"{machine}.{short}", machine, node_id)
                if sig.name in self.signals:
                    raise ValueError(f"signal {sig.name} mapped twice")
                self.signals[sig.name] = sig
                self.by_node[machine, node_id] = sig
        self.values: dict[str, dict[str, str]] = data.get("values", {})
        unknown = [s for s in self.values if s not in self.signals]
        if unknown:
            raise ValueError(f"value maps for unknown signals: {unknown}")

    def machines(self) -> list[str]:
        return sorted(self.data.get("machines", {}))

    def server(self, machine: str) -> str:
        """The real server (simulator machine) of a logical machine."""
        return self.data["machines"][machine]["server"]

    def signal_of(self, machine: str, node_id: str) -> Signal | None:
        return self.by_node.get((machine, node_id))

    def logical_value(self, signal: str, value: Any) -> Any:
        """Numbers and booleans pass through. A string becomes its logical name from the signal's value map;
        any other string (no map, or not in the map) becomes "unmapped:<hash>", so no real text leaves the
        collector. The empty string stays empty (it means "no mission")."""
        table = self.values.get(signal, {})
        if isinstance(value, list):          # a list of codes (alarm numbers): each one mapped
            return [table.get(str(v), f"unmapped:{hashlib.sha256(str(v).encode()).hexdigest()[:8]}") for v in value]
        if not isinstance(value, str) or value == "":
            return value
        return table.get(value, f"unmapped:{hashlib.sha256(value.encode()).hexdigest()[:8]}")

    def hash(self) -> str:
        return hashlib.sha256(json.dumps(self.data, sort_keys=True).encode()).hexdigest()[:16]


def load_mapping(path: Path | None = None) -> tuple[Mapping, Path]:
    """The local mapping if it exists, else the example one (for the invented fixture)."""
    path = Path(path) if path else (LOCAL_MAPPING if LOCAL_MAPPING.exists() else EXAMPLE_MAPPING)
    return Mapping(json.loads(path.read_text(encoding="utf-8"))), path
