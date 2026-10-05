from raglab.checks import fake_hits, run_checks
from raglab.context import build_context
from raglab.generation import check_citations


def checks(exe, check):
    context = build_context(fake_hits("lx40-cooling-1", "p3-temps-1"), 1500)
    check.ok(context.ids == ["lx40-cooling-1", "p3-temps-1"], "the context keeps the retrieved chunks in rank order")
    check.ok(check_citations("Keep it between 15 and 22 °C. [lx40-cooling-1]", context.ids).ok,
             "an answer that cites a chunk from the context passes the citation check")
    check.ok(not check_citations("Keep it cold.", context.ids).ok, "an answer without citations fails")
    check.ok(check_citations("Not in the manuals.", context.ids).ok, "the refusal passes")
    check.ok("[" in exe.SYSTEM_PROMPT, "the system prompt asks for [id] citations")


run_checks(checks, __file__.replace("check.py", "exe00.py"))
