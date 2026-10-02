from declab.checks import fake_choice, fake_noul, fake_score, run_checks


def checks(exe, check):
    component = check.question(exe.QUESTIONS, "component", "choice")
    severity = check.question(exe.QUESTIONS, "severity", "score")
    reproducible = check.question(exe.QUESTIONS, "reproducible", "noul")
    if not (component and severity and reproducible):
        return
    check.ok(component.get("criteria") == exe.COMPONENTS, "'component' uses COMPONENTS", component.get("criteria"))
    check.ok(severity.get("criteria") == exe.SEVERITY, "'severity' uses SEVERITY, in order", severity.get("criteria"))
    check.valid(exe.CASES[0], exe.QUESTIONS)

    def answers(component_name, severity_probabilities, reproducible_p):
        probabilities = {key: 0.01 for key in exe.COMPONENTS}
        probabilities[component_name] = 1 - 0.01 * (len(exe.COMPONENTS) - 1)
        return {
            "component": fake_choice(probabilities),
            "severity": fake_score(severity_probabilities, exe.SEVERITY),
            "reproducible": fake_noul(reproducible_p),
        }

    for case, expected, note in [
        (answers("database", [0, 0, 0.1, 0.9], 0.1), "page the on-call engineer (database)", "critical -> page, even without steps"),
        (answers("frontend", [0.1, 0.8, 0.1, 0], 0.9), "add to the frontend backlog", "minor + reproducible -> backlog"),
        (answers("frontend", [0.5, 0.5, 0, 0], 0.2), "ask the reporter for steps and the error message", "minor, no steps -> ask"),
        (answers("unknown", [0, 0.5, 0.5, 0], 0.9), "ask the reporter for steps and the error message", "unknown component -> ask"),
        (answers("backend", [0, 0, 0.5, 0.5], 0.9), "page the on-call engineer (backend)", "severity 2.5 -> page"),
    ]:
        done, action = check.calls(exe.act, "any report", case)
        if not done:
            return
        check.ok(action == expected, note, action)


run_checks(checks, __file__.replace("check.py", "exe06.py"))
