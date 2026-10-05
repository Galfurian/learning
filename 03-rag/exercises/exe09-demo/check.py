import json

from raglab.checks import run_checks
from raglab.corpus import PLANT_HOLDOUT, PLANT_MANUALS, load_manuals


def checks(exe, check):
    sections = load_manuals(PLANT_MANUALS)
    ids = {s.id for s in sections}
    check.ok(len(sections) >= 288, "the plant manuals are built", len(sections))
    holdout = json.loads(PLANT_HOLDOUT.read_text())
    check.ok(len(holdout) == 20, "the holdout set has 20 questions", len(holdout))
    for q in holdout:
        text = " ".join(s.text for s in sections if s.id in q["relevant"]).lower()
        check.ok(set(q["relevant"]) <= ids and all(n.lower() in text for n in q["must_contain"]),
                 f"{q['id']}: labels point at real sections that contain {q['must_contain']}")
    check.ok(sum(not q["relevant"] for q in holdout) == 3, "3 no-answer questions")
    context = exe.stuffed_context(sections)
    check.ok(0 < len(context.chunks) < len(sections), "--mode stuff fits only part of the manuals", len(context.chunks))


run_checks(checks, __file__.replace("check.py", "exe09.py"))
