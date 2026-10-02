from declab.checks import fake_choice, fake_noul, run_checks


def checks(exe, check):
    # The request contract: well formed, without any model.
    team = check.question(exe.QUESTIONS, "team", "choice")
    check.question(exe.QUESTIONS, "refund", "noul")
    check.valid(exe.CASES[0], exe.QUESTIONS)
    if team is not None:
        check.ok(
            set(team["criteria"]) == set(exe.QUEUES),
            "every option of 'team' has a queue in QUEUES",
            sorted(team["criteria"]),
        )

    # The application code: fed with fake answers shaped like Ollama's.
    answers = {
        "team": fake_choice({"billing": 0.9, "technical": 0.05, "account": 0.03, "other": 0.02}),
        "refund": fake_noul(0.8),
    }
    action = exe.act("any ticket", answers)
    check.ok(
        action == "put in queue/billing, tagged 'refund-request'",
        "billing + refund 0.8 -> billing queue, tagged",
        action,
    )

    answers["refund"] = fake_noul(0.2)
    action = exe.act("any ticket", answers)
    check.ok(action == "put in queue/billing", "billing + refund 0.2 -> billing queue, no tag", action)


run_checks(checks, __file__.replace("check.py", "exe00.py"))
