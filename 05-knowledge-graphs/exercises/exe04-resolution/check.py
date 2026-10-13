from kglab.checks import run_checks
from kglab.metrics import AMBIGUOUS


def checks(exe, check):
    done, out = check.calls(exe.normalize, "The  First-Rover!")
    if not done:
        return
    check.ok(out == "first rover", "lowercase, punctuation and 'the' out", out)
    check.ok(exe.normalize("NoAirPressure") == "no air pressure", "CamelCase split", exe.normalize("NoAirPressure"))
    check.ok(exe.normalize("bay:5") == "bay:5", "':' stays (node ids)", exe.normalize("bay:5"))
    check.ok(exe.normalize("theater") == "theater", "only a leading word 'the' goes", exe.normalize("theater"))
    exact = {"Rover R-1": {"r1"}, "r1": {"r1"}, "Busy": {"a/Busy", "b/Busy"}}
    normal = {"rover r 1": {"r1"}, "first rover": {"r1"}, "busy": {"a/Busy", "b/Busy"}, "rover": {"r1", "r2"}}
    done, out = check.calls(exe.resolve, "Rover R-1", exact, normal)
    if not done:
        return
    check.ok(out == ("r1", "exact"), "exact name", out)
    check.ok(exe.resolve("the first rover", exact, normal) == ("r1", "normalized"), "alias, normalized",
             exe.resolve("the first rover", exact, normal))
    check.ok(exe.resolve("Busy", exact, normal) == (AMBIGUOUS, "ambiguous"), "two exact hits: ambiguous",
             exe.resolve("Busy", exact, normal))
    check.ok(exe.resolve("the rover", exact, normal) == (AMBIGUOUS, "ambiguous"), "two normalized hits: ambiguous",
             exe.resolve("the rover", exact, normal))
    check.ok(exe.resolve("the crane", exact, normal) == (None, "none"), "nothing: None",
             exe.resolve("the crane", exact, normal))


run_checks(checks, __file__.replace("check.py", "exe04.py"))
