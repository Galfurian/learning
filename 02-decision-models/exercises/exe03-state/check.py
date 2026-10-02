from declab.checks import run_checks


def checks(exe, check):
    for index, record in enumerate(exe.CASES, start=1):
        done, state = check.calls(exe.build_state, record)
        if not done:
            return
        expected = "\n".join(
            f"{exe.SPEAKERS[speaker]}: {text}" for speaker, text in record["thread"]
        )
        check.ok(state == expected, f"case {index}: the state is the whole conversation, in order", state)

        text = state if isinstance(state, str) else str(state)
        leaked = [
            value for value in record["customer"].values() if str(value).lower() in text.lower()
        ]
        check.ok(not leaked, f"case {index}: no personal data in the state", leaked)

    check.valid(exe.build_state(exe.CASES[0]), exe.QUESTIONS)


run_checks(checks, __file__.replace("check.py", "exe03.py"))
