"""The answer: a generator reads the evidence lines of an order and cites them.

The method of unit 07, an own copy (the unit imports nothing from unit 07).
The generator never reads the log. It reads numbered lines, each with its
claim kind; it must cite an event id for every claim, say "probably" where a
line is inferred, and refuse when the lines do not answer. The checks are code.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from .client import DEFAULT_CHAT_MODEL, Tracer, chat

REFUSAL = "Not in the recording."
MAX_TOKENS = 400

SYSTEM_PROMPT = f"""You answer questions about orders on a production line.
Use only the evidence lines in the user message. A line starts with event ids in square brackets.
After every sentence, write the ids of the lines it uses, for example [e12].
A line marked inferred is not observed: say probably.
A "why" can come only from a line that gives a cause; if no line gives one, say the recording does not show why.
Unusual is a comparison with the baseline on the line, not a cause.
Write two to four sentences in your own words. Do not copy the lines. Cite only ids that appear in the lines.
If the lines do not answer the question, reply exactly: {REFUSAL}"""


def echo(lines: Sequence[str]) -> str:
    """The answer of no model: the evidence lines themselves, or the refusal when no line names an
    event. It is the baseline an LLM must beat: right facts, right ids, but no reply to the question."""
    if not any(line.startswith("[") for line in lines):
        return REFUSAL
    return "\n".join(lines)


def messages(question: str, lines: Sequence[str], system: str = SYSTEM_PROMPT) -> list[dict[str, str]]:
    body = "\n".join(lines) if lines else "(no evidence)"
    return [{"role": "system", "content": system},
            {"role": "user", "content": f"Evidence:\n{body}\n\nQuestion: {question}"}]


@dataclass
class Answer:
    text: str
    cited: list[str]
    unknown: list[str]          # cited ids that are not in the evidence
    refused: bool
    seconds: float


def cited_ids(text: str) -> list[str]:
    found = []
    for inside in re.findall(r"\[([^\[\]]+)\]", text):
        for token in re.split(r"[,;\s]+", inside.strip()):
            if re.fullmatch(r"e\d+", token) and token not in found:
                found.append(token)
    return found


def line_ids(lines: Sequence[str]) -> set[str]:
    return {i for line in lines for i in cited_ids(line.split("]")[0] + "]" if line.startswith("[") else "")}


def judge(text: str, lines: Sequence[str], seconds: float = 0.0) -> Answer:
    """The code checks of an answer text against the lines it read."""
    text = text.strip()
    cited = cited_ids(text)
    allowed = line_ids(lines)
    return Answer(text, cited, [c for c in cited if c not in allowed], REFUSAL.lower().rstrip(".") in text.lower(),
                  seconds)


def answer(question: str, lines: Sequence[str], *, model: str = DEFAULT_CHAT_MODEL,
           tracer: Tracer | None = None, system: str = SYSTEM_PROMPT) -> Answer:
    result = chat(model, messages(question, lines, system), max_tokens=MAX_TOKENS, tracer=tracer)
    return judge(result.content, lines, result.seconds)


def mentions_inference(text: str) -> bool:
    return bool(re.search(r"\b(inferred|probably|likely)\b", text, re.I))
