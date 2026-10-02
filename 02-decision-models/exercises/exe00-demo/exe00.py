"""EXE00 — a solved example. Nothing to write: read it, run it, trace it."""

from declab.exercise import run

# Application data: the support tickets that arrived this morning.
CASES = [
    "Hi, you charged my card twice for the October plan. Please refund one of the payments.",
    "The mobile app crashes every time I open the settings page since the last update.",
    "How do I change the email address on my account?",
]

# What we ask the decision model about every ticket. This is the request
# contract: a name, a type, instructions, and (for choice) the options.
QUESTIONS = {
    "team": {
        "type": "choice",
        "instructions": "Which team should handle this support ticket?",
        "criteria": {
            "billing": "Payments, charges, invoices, refunds.",
            "technical": "Bugs, crashes, errors, things that do not work.",
            "account": "Login, profile, email address, account settings.",
            "other": "Anything that fits none of the teams above.",
        },
    },
    "refund": {
        "type": "noul",
        "instructions": "Does the customer explicitly ask for money back?",
    },
}

QUEUES = {
    "billing": "queue/billing",
    "technical": "queue/engineering",
    "account": "queue/helpdesk",
    "other": "queue/triage",
}


def act(ticket: str, answers: dict) -> str:
    """Application code. The model has decided; here the program acts on it."""
    queue = QUEUES[answers["team"]["choice"]]
    if answers["refund"]["noul"] >= 0.5:
        return f"put in {queue}, tagged 'refund-request'"
    return f"put in {queue}"


if __name__ == "__main__":
    run(QUESTIONS, CASES, __file__, act=act)
