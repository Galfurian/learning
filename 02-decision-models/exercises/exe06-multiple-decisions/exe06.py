"""EXE06 — several decisions about one state. Task: see README.md in this folder."""

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

# TODO: three questions about the same report: "component" (choice over
# COMPONENTS), "severity" (score over SEVERITY), "reproducible" (noul).
QUESTIONS: dict = {}


# TODO: combine the three answers into one action (see README.md).
def act(report: str, answers: dict) -> str:
    raise NotImplementedError


if __name__ == "__main__":
    run(QUESTIONS, CASES, __file__, act=act)
