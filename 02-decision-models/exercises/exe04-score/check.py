from declab.checks import fake_score, run_checks

CALL = "open a support case and call the customer"
THANK = "send a thank-you email"
REFER = "invite the customer to the referral program"


def checks(exe, check):
    satisfaction = check.question(exe.QUESTIONS, "satisfaction", "score")
    if satisfaction is None:
        return
    check.ok(
        satisfaction.get("criteria") == exe.LEVELS,
        "the criteria are LEVELS, in order from worst to best",
        satisfaction.get("criteria"),
    )
    check.valid(exe.CASES[0], exe.QUESTIONS)

    for probabilities, expected, note in [
        ([0.85, 0.15, 0, 0, 0], CALL, "very unhappy (score 0.15)"),
        ([0.1, 0.4, 0.4, 0.1, 0], THANK, "unhappy or neutral (score 1.50 is not below 1.5)"),
        ([0, 0, 1, 0, 0], THANK, "neutral (score 2.00)"),
        ([0, 0, 0, 0.5, 0.5], REFER, "happy or very happy (score 3.50)"),
        ([0.5, 0, 0, 0, 0.5], THANK, "half very unhappy, half very happy (score 2.00!)"),
    ]:
        answer = fake_score(probabilities, exe.LEVELS)
        done, action = check.calls(exe.act, "any review", {"satisfaction": answer})
        if not done:
            return
        check.ok(action == expected, f"{note} -> {expected!r}", action)


run_checks(checks, __file__.replace("check.py", "exe04.py"))
