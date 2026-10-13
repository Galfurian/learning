from evlab.checks import run_checks

NODES = [
    {"path": "a", "node_id": "1", "kind": "numeric", "events_in_trace": 3},
    {"path": "b", "node_id": "2", "kind": "method", "events_in_trace": 0},
    {"path": "c", "node_id": "3", "kind": "boolean", "events_in_trace": 0},
    {"path": "d", "node_id": "4", "kind": "string", "events_in_trace": 9},
    {"path": "e", "node_id": "5", "kind": "folder", "events_in_trace": 0},
    {"path": "f", "node_id": "6", "kind": "boolean", "events_in_trace": 1},
]


def checks(exe, check):
    done, out = check.calls(exe.select_nodes, NODES)
    if not done:
        return
    paths = [n["path"] for n in out]
    check.ok(paths == ["d", "a", "f"], "variables that change, most events first", paths)
    check.ok(exe.select_nodes([]) == [], "an empty catalog: nothing")


run_checks(checks, __file__.replace("check.py", "exe01.py"))
