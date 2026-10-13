"""EXE01 — the catalog: subscribe only to what moves. Task: see README.md in this folder."""

from typing import Any

from evlab.runners import run_select


# TODO: keep the nodes worth a subscription.
# Each node is a dict from the simulator's catalog: {"path", "node_id", "kind", "events_in_trace", ...}.
# - keep variables only: kind "boolean", "numeric" or "string" (not "method", "folder", "object");
# - keep only the nodes whose value changes in the trace: events_in_trace > 0;
# - return them sorted by events_in_trace, most first.
def select_nodes(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_select(select_nodes, __file__)
