"""EXE04 — a score on an ordered scale. Task: see README.md in this folder."""

from declab.exercise import run

# Application data: product reviews published this week.
CASES = [
    "Absolutely love it, best purchase this year!",
    "It works, nothing special.",
    "Broke after two days and support never answered. Never again.",
    "Good quality but the delivery was late.",
]

# The scale, from worst to best. The order is the meaning.
LEVELS = ["Very unhappy", "Unhappy", "Neutral", "Happy", "Very happy"]

# TODO: add one 'score' question named "satisfaction" that uses LEVELS.
QUESTIONS: dict = {}


# TODO: map the score to an action (see the table in README.md).
def act(review: str, answers: dict) -> str:
    raise NotImplementedError


if __name__ == "__main__":
    run(QUESTIONS, CASES, __file__, act=act)
