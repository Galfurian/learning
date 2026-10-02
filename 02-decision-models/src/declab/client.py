"""The whole decision-model API is one HTTP request.

There is no SDK on purpose: the request and the response are plain JSON, and
seeing them is half of the lesson.
"""

import json
import time
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DECIDE_URL = "http://127.0.0.1:11434/v1/systemone"
DEFAULT_MODEL = "tev1:4b-q4_K_M"


class DecisionError(RuntimeError):
    """Ollama rejected the request, or could not be reached."""


@dataclass
class Decision:
    """What came back from one call, plus how long it took."""

    answers: dict[str, dict[str, Any]]
    usage: dict[str, int]
    seconds: float
    raw: dict[str, Any]


def request_body(model: str, state: Any, questions: dict[str, Any]) -> dict[str, Any]:
    return {"model": model, "state": state, "questions": questions}


def decide(
    state: Any,
    questions: dict[str, Any],
    *,
    model: str = DEFAULT_MODEL,
    url: str = DECIDE_URL,
    timeout: float = 300,
) -> Decision:
    """Ask the decision model every question in ``questions`` about ``state``."""
    body = request_body(model, state, questions)
    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.perf_counter()
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = json.load(response)
    except HTTPError as exc:
        # Ollama explains what is wrong in the body: {"error": "..."}.
        try:
            message = json.load(exc).get("error", str(exc))
        except (json.JSONDecodeError, AttributeError):
            message = str(exc)
        raise DecisionError(message) from exc
    except URLError as exc:
        raise DecisionError(
            f"cannot reach Ollama at {url} ({exc.reason}). Is `ollama serve` running?"
        ) from exc
    return Decision(
        answers=raw.get("answers", {}),
        usage=raw.get("usage", {}),
        seconds=time.perf_counter() - started,
        raw=raw,
    )


def decide_each(
    state: Any,
    questions: dict[str, Any],
    *,
    model: str = DEFAULT_MODEL,
    url: str = DECIDE_URL,
    on_request: Any = None,
) -> Decision:
    """Ask every question in its own request, so no question sees another one.

    ``on_request(body, decision)`` is called after each request, for tracing.
    """
    answers: dict[str, dict[str, Any]] = {}
    usage = {"input_tokens": 0, "output_tokens": 0}
    seconds = 0.0
    raws = []
    for name, question in questions.items():
        one = decide(state, {name: question}, model=model, url=url)
        if on_request is not None:
            on_request(request_body(model, state, {name: question}), one)
        answers.update(one.answers)
        for key in usage:
            usage[key] += one.usage.get(key, 0)
        seconds += one.seconds
        raws.append(one.raw)
    return Decision(answers=answers, usage=usage, seconds=seconds, raw={"responses": raws})
