from declab.checks import fake_noul, run_checks


def checks(exe, check):
    meeting = check.question(exe.QUESTIONS, "meeting", "noul")
    if meeting is None:
        return
    check.ok(
        isinstance(meeting.get("instructions"), str) and meeting["instructions"].strip().endswith("?"),
        "'meeting' has instructions phrased as a yes/no question",
        meeting.get("instructions"),
    )
    check.valid(exe.CASES[0], exe.QUESTIONS)

    for probability, expected in [(0.97, "calendar"), (0.5, "calendar"), (0.49, "inbox"), (0.03, "inbox")]:
        done, action = check.calls(exe.act, "any email", {"meeting": fake_noul(probability)})
        if not done:
            return
        check.ok(action == expected, f"P(meeting)={probability} -> {expected!r}", action)


run_checks(checks, __file__.replace("check.py", "exe01.py"))
