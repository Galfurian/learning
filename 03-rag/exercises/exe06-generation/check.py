import json
from pathlib import Path

from raglab.checks import run_checks
from raglab.generation import REFUSAL


def checks(exe, check):
    prompt = exe.SYSTEM_PROMPT
    check.ok(REFUSAL in prompt, "the prompt tells the model the exact refusal text")
    check.ok("[" in prompt and "]" in prompt, "the prompt shows the [id] citation format")
    check.ok("only" in prompt.lower(), "the prompt says to use only the excerpts")
    ids = ["lx40-cooling-1", "p3-temps-1"]
    done, report = check.calls(exe.check_citations, "Keep it between 15 and 22 °C. [lx40-cooling-1]", ids)
    if not done:
        return
    check.ok(report.ok and report.cited == ["lx40-cooling-1"], "a citation from the context passes", report)
    multi = exe.check_citations("Yes [lx40-cooling-1, p3-temps-1].", ids)
    check.ok(multi.ok and multi.cited == ids, "several ids in one bracket are all read", multi)
    bad = exe.check_citations("Yes. [rf9-profile-1]", ids)
    check.ok(not bad.ok and bad.unknown == ["rf9-profile-1"], "an id outside the context fails", bad)
    check.ok(exe.check_citations("Yes.", ids).problem == "no citations", "no citation fails")
    check.ok(exe.check_citations(REFUSAL, ids).ok, "the refusal passes")
    check.ok(not exe.check_citations(f"{REFUSAL} [p3-temps-1]", ids).ok, "a refusal with citations fails")
    recorded = Path(__file__).with_name("recorded.json")
    if recorded.exists():
        case = json.loads(recorded.read_text())
        check.ok(exe.check_citations(case["answer"], case["context_ids"]).ok,
                 "the recorded WRONG answer passes too: a citation that exists is not a citation that supports")


run_checks(checks, __file__.replace("check.py", "exe06.py"))
