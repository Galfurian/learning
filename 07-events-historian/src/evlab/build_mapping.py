"""Build the local mapping (logical name -> real node id) from the simulator's catalog.

Input: .local/patterns.json (git-ignored), written by whoever has access to
the line: for each logical signal, the end of its real path; for each logical
value, the real value. Output: .local/mapping.json (git-ignored). The
builder refuses to write anywhere else, so real ids never reach a tracked file.
"""

import json
from pathlib import Path
from typing import Any

from .mapping import LOCAL_MAPPING, UNIT_ROOT, Mapping

LOCAL_DIR = UNIT_ROOT / ".local"
PATTERNS = LOCAL_DIR / "patterns.json"


def resolve(patterns: dict[str, Any], catalog: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """catalog: real server name -> its nodes ({"path", "node_id"}). Each pattern must match exactly one path end."""
    out: dict[str, Any] = {"machines": {}, "values": patterns.get("values", {})}
    problems = []
    for machine, spec in patterns["machines"].items():
        nodes = catalog.get(spec["server"], [])
        signals = {}
        for short, suffix in spec["signals"].items():
            hits = [n for n in nodes if n["path"].endswith(suffix)]
            if len(hits) != 1:
                problems.append(f"{machine}.{short}: {len(hits)} nodes end with the pattern")
                continue
            signals[short] = hits[0]["node_id"]
        out["machines"][machine] = {"server": spec["server"], "signals": signals}
    if problems:
        raise ValueError("cannot build the mapping:\n" + "\n".join(problems))
    Mapping(out)   # validate
    return out


def write_local(mapping: dict[str, Any], path: Path = LOCAL_MAPPING) -> Path:
    path = Path(path).resolve()
    if LOCAL_DIR.resolve() not in path.parents:
        raise ValueError(f"the real mapping goes only under {LOCAL_DIR}, not {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(mapping, indent=1) + "\n", encoding="utf-8")
    return path
