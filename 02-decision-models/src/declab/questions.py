"""Rules a request must follow, checked locally before anything is sent.

They mirror the errors Ollama returns for ``/v1/systemone``, so ``--inspect``
and ``check.py`` can catch a malformed question without a model.
"""

import math
from typing import Any

TYPES = ("noul", "choice", "score")
MAX_QUESTIONS = 64
MIN_OPTIONS, MAX_OPTIONS = 2, 26


def problems(state: Any, questions: Any) -> list[str]:
    """Return what is wrong with this request; an empty list means it is valid."""
    found: list[str] = []
    if state is None or state == "" or state == {} or state == []:
        found.append("state must not be empty")
    elif not isinstance(state, (str, dict, list)):
        found.append("state must be a string, object, or array")

    if not isinstance(questions, dict) or not 1 <= len(questions) <= MAX_QUESTIONS:
        found.append(f"questions must contain 1–{MAX_QUESTIONS} fields")
        return found

    for name, question in questions.items():
        found += [f"question {name!r}: {issue}" for issue in _question_problems(question)]
    return found


def _question_problems(question: Any) -> list[str]:
    if not isinstance(question, dict):
        return ["must be an object"]
    kind = question.get("type")
    if kind not in TYPES:
        return ["type must be choice, noul, or score"]

    found = []
    if not question.get("instructions"):
        found.append("instructions must be a nonempty string")

    criteria = question.get("criteria")
    if kind == "noul":
        if criteria is not None and (
            not isinstance(criteria, dict) or not set(criteria) <= {"true", "false"}
        ):
            found.append("noul criteria must be an object of true/false descriptions")
    elif kind == "choice":
        if not isinstance(criteria, dict):
            found.append("choice criteria must map option keys to descriptions or null")
        elif not MIN_OPTIONS <= len(criteria) <= MAX_OPTIONS:
            found.append(f"criteria must contain {MIN_OPTIONS}–{MAX_OPTIONS} candidates")
    elif kind == "score":
        if not isinstance(criteria, list):
            found.append("score criteria must be an array of descriptions")
        elif not MIN_OPTIONS <= len(criteria) <= MAX_OPTIONS:
            found.append(f"criteria must contain {MIN_OPTIONS}–{MAX_OPTIONS} candidates")
    return found


def entropy_confidence(probabilities: dict[str, float]) -> float:
    """1 - normalized entropy: 1 when one option has all the mass, 0 when uniform.

    This is the ``confidence`` Ollama reports for ``choice`` and ``score``.
    """
    values = [p for p in probabilities.values() if p > 0]
    if len(probabilities) < 2:
        return 1.0
    entropy = -sum(p * math.log(p) for p in values)
    return 1 - entropy / math.log(len(probabilities))
