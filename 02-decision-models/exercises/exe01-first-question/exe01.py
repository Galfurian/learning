"""EXE01 — your first question. Task: see README.md in this folder."""

from declab.exercise import run

# Application data: emails that arrived in Anna's inbox.
CASES = [
    "Hi Anna, could we meet on Thursday at 10 to go through the budget? Let me know if that works.",
    "Attached is the final version of the report. No changes needed from your side.",
    "Thanks for yesterday's call, it was very useful.",
    "Are you around sometime next week? There's something I'd like to discuss with you in person.",
]

# TODO: add one 'noul' question named "meeting".
QUESTIONS: dict = {}

THRESHOLD = 0.5


# TODO: return "calendar" when the email asks for a meeting, else "inbox".
def act(email: str, answers: dict) -> str:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run(QUESTIONS, CASES, __file__, act=act)
