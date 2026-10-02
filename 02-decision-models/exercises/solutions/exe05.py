"""EXE05 — solution."""

import math

from declab.exercise import run

# Application data: forum posts waiting for moderation.
CASES = [
    "Does anyone know how to reset the router to factory settings? Thanks!",
    "BUY CHEAP WATCHES NOW!!! visit cheap-watchez.biz for 90% off",
    "You are an idiot and everyone here hates you.",
    "This tutorial is garbage, whoever wrote it should be fired.",
    "Great guide! I also wrote about this on my blog, link in my profile.",
]

QUESTIONS = {
    "kind": {
        "type": "choice",
        "instructions": "What kind of forum post is this?",
        "criteria": {
            "normal": "A question, an answer, or an opinion.",
            "spam": "An advertisement for a product or a website.",
            "insult": "The post insults or attacks a person.",
        },
    },
}

# How sure the model must be before the APP acts alone. A wrong "delete" or
# "hide" hurts a real user, so those need more evidence than "publish".
THRESHOLDS = {
    "normal": 0.8,
    "spam": 0.9,
    "insult": 0.9,
}

ACTIONS = {
    "normal": "publish",
    "spam": "delete",
    "insult": "hide and warn the author",
}


def confidence(probabilities: dict[str, float]) -> float:
    entropy = -sum(p * math.log(p) for p in probabilities.values() if p > 0)
    return 1 - entropy / math.log(len(probabilities))


def margin(probabilities: dict[str, float]) -> float:
    first, second = sorted(probabilities.values(), reverse=True)[:2]
    return first - second


def act(post: str, answers: dict) -> str:
    kind = answers["kind"]
    choice = kind["choice"]
    probabilities = kind["probabilities"]
    evidence = (
        f"p={probabilities[choice]:.2f}, confidence {confidence(probabilities):.2f}, "
        f"margin {margin(probabilities):.2f}"
    )
    if probabilities[choice] < THRESHOLDS[choice]:
        return f"send to a human moderator ({choice}? {evidence})"
    return f"{ACTIONS[choice]} ({evidence})"


if __name__ == "__main__":
    run(QUESTIONS, CASES, __file__, act=act)
