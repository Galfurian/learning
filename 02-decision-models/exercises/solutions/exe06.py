"""EXE06 — solution."""

from declab.exercise import run

# Application data: bug reports opened today.
CASES = [
    "The production database is down and no customer can log in.",
    (
        "The export button produces a CSV with the wrong date format. Steps: open Reports, "
        "pick any month, click Export. The dates come out as MM/DD instead of DD/MM."
    ),
    "Something is weird with the dashboard, it looks off sometimes.",
    (
        "Checkout fails for some customers paying with PayPal: they get error 502 after "
        "confirming the payment. Card payments work."
    ),
]

COMPONENTS = {
    "frontend": "Web pages, buttons, layout, what the user sees.",
    "backend": "Servers, APIs, payments, errors returned by the service.",
    "database": "Stored data, queries, the database server.",
    "unknown": "The report does not say enough to tell.",
}

SEVERITY = [
    "Cosmetic: nothing is broken",
    "Minor: something is wrong, there is a workaround",
    "Major: a feature is broken for some users",
    "Critical: the whole service is down",
]

QUESTIONS = {
    "component": {
        "type": "choice",
        "instructions": "Which part of the system is the bug report about?",
        "criteria": COMPONENTS,
    },
    "severity": {
        "type": "score",
        "instructions": "How severe is the problem described in the bug report?",
        "criteria": SEVERITY,
    },
    "reproducible": {
        "type": "noul",
        "instructions": "Does the report say what the user did, or which error they got?",
    },
}


def act(report: str, answers: dict) -> str:
    component = answers["component"]["choice"]
    severity = answers["severity"]["score"]
    reproducible = answers["reproducible"]["noul"] >= 0.5

    if severity >= 2.5:
        return f"page the on-call engineer ({component})"
    if not reproducible or component == "unknown":
        return "ask the reporter for steps and the error message"
    return f"add to the {component} backlog"


if __name__ == "__main__":
    run(QUESTIONS, CASES, __file__, act=act)
