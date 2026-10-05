import json
from pathlib import Path

from raglab.checks import run_checks


def trace(relevant, hits, context, answer="x [a-1]", abstained=False, correct=True, supported=True):
    return {"relevant": relevant, "answer": answer, "abstained": abstained,
            "hits": [{"id": f"{s}-1", "section_id": s, "score": 0.5, "rank": r} for r, s in enumerate(hits, 1)],
            "context": [{"id": f"{s}-1", "section_id": s} for s in context],
            "labels": {"answer_correct": correct, "supported": supported}}


CASES = [
    (trace(["a"], ["b", "c"], ["b", "c"]), "RETRIEVAL", "no relevant hit"),
    (trace(["a"], ["b", "a"], ["b"]), "CONTEXT", "relevant hit dropped from the context"),
    (trace(["a"], ["a"], ["a"], correct=False), "GENERATION", "right chunk read, wrong answer"),
    (trace(["a"], ["a"], ["a"], supported=False), "GENERATION", "right answer, citation does not support it"),
    (trace(["a"], ["a"], ["a"]), "NONE", "correct and supported"),
    (trace(["a"], ["b"], [], answer="Not in the manuals.", abstained=True, correct=False), "RETRIEVAL",
     "retrieval failed first, even though the app abstained"),
    (trace([], ["b"], ["b"], answer="Not in the manuals.", correct=None, supported=None), "NONE", "no answer exists, refused"),
    (trace([], ["b"], [], answer="Not in the manuals.", abstained=True, correct=None, supported=None), "NONE", "no answer exists, app abstained"),
    (trace([], ["b"], ["b"], answer="Two years. [b-1]", correct=None, supported=None), "GENERATION", "no answer exists, answered anyway"),
]


def checks(exe, check):
    done, _ = check.calls(exe.diagnose, CASES[0][0])
    if not done:
        return
    for case, expected, why in CASES:
        found = exe.diagnose(case)
        check.ok(found == expected, f"{expected:<10} {why}", found)
    for path in sorted(Path(__file__).with_name("traces").glob("*.json")):
        recorded = json.loads(path.read_text())
        check.ok(exe.diagnose(recorded) == recorded["expected"], f"recorded {path.stem} -> {recorded['expected']}")


run_checks(checks, __file__.replace("check.py", "exe08.py"))
