"""EXE01 — solution."""

from declab.exercise import run

# Application data: emails that arrived in Anna's inbox.
CASES = [
    "Hi Anna, could we meet on Thursday at 10 to go through the budget? Let me know if that works.",
    "Attached is the final version of the report. No changes needed from your side.",
    "Thanks for yesterday's call, it was very useful.",
    "Are you around sometime next week? There's something I'd like to discuss with you in person.",
]

QUESTIONS = {
    "meeting": {
        "type": "noul",
        "instructions": "Is the sender asking to schedule a meeting?",
    },
}

THRESHOLD = 0.5


def act(email: str, answers: dict) -> str:
    if answers["meeting"]["noul"] >= THRESHOLD:
        return "calendar"
    return "inbox"


if __name__ == "__main__":
    run(QUESTIONS, CASES, __file__, act=act)
