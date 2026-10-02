"""EXE05 — probabilities and confidence. Task: see README.md in this folder."""

import math  # noqa: F401  (you need it for confidence())

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


# TODO: 1 - entropy / log(number of options). Do not read answer["confidence"].
def confidence(probabilities: dict[str, float]) -> float:
    raise NotImplementedError


# TODO: probability of the best option minus probability of the second best.
def margin(probabilities: dict[str, float]) -> float:
    raise NotImplementedError


# TODO: act alone only above the threshold of the chosen option.
def act(post: str, answers: dict) -> str:
    raise NotImplementedError


if __name__ == "__main__":
    run(QUESTIONS, CASES, __file__, act=act)
