from kglab.checks import run_checks


CASES = [
    ("Which devices serve bay 9?", ("bay 9",), ("^serves_bay",), "list"),
    ("How many devices serve bay 9?", ("bay 9",), ("^serves_bay",), "count"),
    ("Which folder exposes the MovePallet?", ("MovePallet",), ("^exposes_variable",), "list"),
]


def checks(exe, check):
    done, out = check.calls(exe.plan, CASES[0][0])
    if not done:
        return
    for question, start, path, op in CASES:
        found = exe.plan(question)
        check.ok(found is not None, f"plan exists: {question}", found)
        if found is not None:
            check.ok(found.start == start, f"start mention: {question}", found.start)
            check.ok(found.path == path, f"relation path: {question}", found.path)
            check.ok(found.op == op, f"operation: {question}", found.op)
    check.ok(exe.plan("Tell me the maintenance phone number.") is None, "unknown question returns None",
             exe.plan("Tell me the maintenance phone number."))


run_checks(checks, __file__.replace("check.py", "exe05.py"))
