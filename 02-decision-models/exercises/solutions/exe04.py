"""EXE04 — solution."""

from declab.exercise import run

# Application data: product reviews published this week.
CASES = [
    "Absolutely love it, best purchase this year!",
    "It works, nothing special.",
    "Broke after two days and support never answered. Never again.",
    "Good quality but the delivery was late.",
]

LEVELS = ["Very unhappy", "Unhappy", "Neutral", "Happy", "Very happy"]

QUESTIONS = {
    "satisfaction": {
        "type": "score",
        "instructions": "How satisfied is the reviewer with the product?",
        "criteria": LEVELS,
    },
}


def act(review: str, answers: dict) -> str:
    score = answers["satisfaction"]["score"]
    if score < 1.5:
        return "open a support case and call the customer"
    if score >= 3.5:
        return "invite the customer to the referral program"
    return "send a thank-you email"


if __name__ == "__main__":
    run(QUESTIONS, CASES, __file__, act=act)
