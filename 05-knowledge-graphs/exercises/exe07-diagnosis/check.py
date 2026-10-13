from kglab.checks import run_checks


def row(**changes):
    base = {
        "answerable": True,
        "nodes": ["bay:5"],
        "answer_ok": True,
        "path_ok": True,
        "starts": ["bay:5"],
        "gold_starts": ["bay:5"],
        "missing_edges": [],
        "dropped_relations": [],
    }
    base.update(changes)
    return base


CASES = [
    (row(answerable=False, nodes=["wrong"], answer_ok=False), "PLAN", "unanswerable but nodes were returned"),
    (row(answerable=False, nodes=[], answer_ok=True), "NONE", "correct refusal"),
    (row(answerable=False, nodes=[], answer_ok=False), "GENERATION", "unanswerable but answered"),
    (row(missing_edges=[["r1", "serves_bay", "b5", "chunk-a"]],
         dropped_relations=[["chunk-a", "serves_bay"]]), "RESOLUTION", "dropped mention"),
    (row(missing_edges=[["r1", "serves_bay", "b5", "chunk-a"]]), "EXTRACTION", "missing extraction"),
    (row(path_ok=False), "PLAN", "wrong relation path"),
    (row(starts=["b1"], gold_starts=["b5"]), "LINKING", "wrong start node"),
    (row(answer_ok=False), "GENERATION", "right graph, wrong answer"),
    (row(), "NONE", "all stages passed"),
]


def checks(exe, check):
    done, _ = check.calls(exe.diagnose, CASES[0][0])
    if not done:
        return
    for record, expected, why in CASES:
        found = exe.diagnose(record)
        check.ok(found == expected, f"{expected:<10} {why}", found)


run_checks(checks, __file__.replace("check.py", "exe07.py"))
