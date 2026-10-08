import json
from pathlib import Path

from reranklab.checks import run_checks


def r(cands, top, answerable=True, facts=True, citations=True, refused=False):
    return {"answerable": answerable, "facts": facts, "citations_ok": citations, "refused": refused,
            "candidates": [{"gain": g} for g in cands], "top": [{"gain": g} for g in top]}


CASES = [
    (r([0, 1], [1, 0]), "CANDIDATES", "no evidence among the N candidates"),
    (r([0, 2, 0], [0, 0]), "RERANK", "evidence among the candidates, cut by the reranker"),
    (r([2], [2], facts=False), "GENERATION", "evidence read, wrong answer"),
    (r([2], [2], citations=False), "GENERATION", "evidence read, unsupported citation"),
    (r([2], [2]), "NONE", "evidence read, answer correct"),
    (r([0, 1], [0], facts=False), "CANDIDATES", "first failure wins, even if the answer also failed"),
    (r([0], [0], answerable=False, refused=True), "NONE", "no answer exists, refused"),
    (r([0], [0], answerable=False, refused=False), "GENERATION", "no answer exists, answered anyway"),
]


def checks(exe, check):
    done, _ = check.calls(exe.diagnose, CASES[0][0])
    if not done:
        return
    for case, expected, why in CASES:
        found = exe.diagnose(case)
        check.ok(found == expected, f"{expected:<10} {why}", found)
    for path in sorted(Path(__file__).with_name("rows").glob("*.json")):
        record = json.loads(path.read_text())
        check.ok(exe.diagnose(record) == record["expected"], f"recorded {path.stem} -> {record['expected']}")


run_checks(checks, __file__.replace("check.py", "exe07.py"))
