from declab.checks import fake_choice, run_checks


def checks(exe, check):
    queue = check.question(exe.QUESTIONS, "queue", "choice")
    if queue is None:
        return
    criteria = queue.get("criteria") or {}
    check.ok(
        set(criteria) == set(exe.QUEUES),
        "the options are exactly the keys of QUEUES (printer, network, account, hardware, none)",
        sorted(criteria),
    )
    check.ok(
        all(isinstance(text, str) and text.strip() for text in criteria.values()),
        "every option has a description",
        criteria,
    )
    check.valid(exe.CASES[0], exe.QUESTIONS)

    for option in exe.QUEUES:
        probabilities = {key: 0.02 for key in exe.QUEUES}
        probabilities[option] = 1 - 0.02 * (len(exe.QUEUES) - 1)
        done, action = check.calls(exe.act, "any request", {"queue": fake_choice(probabilities)})
        if not done:
            return
        check.ok(action == exe.QUEUES[option], f"choice {option!r} -> {exe.QUEUES[option]!r}", action)


run_checks(checks, __file__.replace("check.py", "exe02.py"))
