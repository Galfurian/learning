"""EXE01 — the catalog: subscribe only to what moves. Reference solution."""

from typing import Any

from evlab.runners import run_select


def select_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    keep = [n for n in nodes if n.get("kind") in ("boolean", "numeric", "string") and (n.get("events_in_trace") or 0) > 0]
    return sorted(keep, key=lambda n: -n["events_in_trace"])


if __name__ == "__main__":
    run_select(select_nodes, __file__)
