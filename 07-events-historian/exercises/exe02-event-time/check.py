from evlab.checks import run_checks

POLLS = [(100.0, 0.0), (101.0, 5.0), (102.0, 10.0)]


def checks(exe, check):
    done, out = check.calls(exe.place, 100.5, POLLS)
    if not done:
        return
    check.ok(out == (2.5, 0.0, 5.0), "between two polls: interpolated, with the two positions as bounds", out)
    check.ok(exe.place(99.0, POLLS) == (0.0, 0.0, 0.0), "before the first poll: the first position")
    check.ok(exe.place(103.0, POLLS) == (10.0, 10.0, 10.0), "after the last poll: the last position")
    check.ok(exe.place(101.0, POLLS)[0] == 5.0, "exactly on a poll: its position")


run_checks(checks, __file__.replace("check.py", "exe02.py"))
