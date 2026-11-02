from collections import Counter

from pmlab.checks import run_checks
from pmlab.compile import play_out
from pmlab.recipes import Operation, Recipe
from pmlab.reference import pm4py, to_pm4py


def op(name, depends=(), branch="main"):
    return Operation(name, 0, 10.0, 5.0, {}, tuple(depends), branch, ())


# a, then b and c in parallel, then d. x is the fail branch of c: after x, c runs again.
TOY = Recipe("toy", (op("a"), op("b", ["a"]), op("c", ["a"]), op("x", ["c"], "fail"), op("d", ["b", "c"])))
LINE = Recipe("line", (op("p"), op("q", ["p"]), op("r", ["q"])))
TWO_STARTS = Recipe("two_starts", (op("p"), op("q"), op("r", ["p", "q"])))


def sound(net):
    ok, _ = pm4py.analysis.check_soundness(*to_pm4py(net))
    return ok


def checks(exe, check):
    done, net = check.calls(exe.compile_recipe, TOY)
    if not done:
        return
    labels = sorted(label for label in net.transitions.values() if label)
    check.ok(labels == ["a", "b", "c", "d", "x"], "one labelled transition per operation", labels)
    check.ok(net.initial == Counter({"source": 1}) and net.final == Counter({"sink": 1}),
             "one token in source; the end is one token in sink")
    lang = play_out(net, max_len=6)
    check.ok({("a", "b", "c", "d"), ("a", "c", "b", "d")} <= lang, "b and c run in either order",
             sorted(lang))
    check.ok(("a", "c", "x", "c", "b", "d") in lang and ("a", "b", "c", "x", "c", "d") in lang,
             "after the fail branch x, c runs again")
    check.ok(not any(s.count("x") > s.count("c") - 1 for s in lang), "x never runs without a c before it again")
    check.ok(len(lang) == 6, "the language up to 6 operations has 6 sequences", sorted(lang))
    check.ok(sound(net), "pm4py: the net is a sound workflow net")

    _, line = check.calls(exe.compile_recipe, LINE)
    check.ok(line is not None and play_out(line) == {("p", "q", "r")}, "a linear recipe has one sequence",
             line and play_out(line))
    _, two = check.calls(exe.compile_recipe, TWO_STARTS)
    check.ok(two is not None and play_out(two) == {("p", "q", "r"), ("q", "p", "r")} and sound(two),
             "two operations with no dependency start together (a silent start)", two and play_out(two))


run_checks(checks, __file__.replace("check.py", "exe05.py"))
