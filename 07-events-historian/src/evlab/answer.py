"""The answer: a generator reads the evidence lines of a chain and cites them.

The generator never reads raw signals. It reads numbered lines, each with its
claim kind; it must cite an event id for every claim, say "inferred" where a
line says so, and refuse when the lines do not answer. The checks are code.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from .causes import explanation_lines
from .chain import Chain, story
from .client import DEFAULT_CHAT_MODEL, Tracer, chat

REFUSAL = "Not in the recording."
MAX_TOKENS = 400

SYSTEM_PROMPT = f"""You answer questions about what happened on a production line.
Use only the evidence lines in the user message. Each line starts with an event id in square brackets.
After every sentence, write the ids of the lines it uses, for example [e12].
A line marked "inferred link to the pallet" is not observed: say "probably" or "inferred" for it.
A "why" can come only from a line marked "cause"; if no such line explains it, say the recording does not show why.
An assignment that is not corroborated is an intention, not a movement.
Write two to four sentences in your own words. Do not copy the lines. Cite only ids that appear in the lines.
If the lines do not answer the question, reply exactly: {REFUSAL}"""


def evidence_lines(chain: Chain) -> list[str]:
    return story(chain) + explanation_lines(chain)


def messages(question: str, chain: Chain | None) -> list[dict[str, str]]:
    body = "\n".join(evidence_lines(chain)) if chain is not None and chain.steps else "(no evidence)"
    return [{"role": "system", "content": SYSTEM_PROMPT},
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


def answer(question: str, chain: Chain | None, *, model: str = DEFAULT_CHAT_MODEL,
           tracer: Tracer | None = None) -> Answer:
    result = chat(model, messages(question, chain), max_tokens=MAX_TOKENS, tracer=tracer)
    text = result.content.strip()
    cited = cited_ids(text)
    allowed = set(chain.ids) if chain is not None else set()
    return Answer(text, cited, [c for c in cited if c not in allowed], REFUSAL.lower().rstrip(".") in text.lower(),
                  result.seconds)


def mentions_inference(text: str) -> bool:
    return bool(re.search(r"\b(inferred|probably|likely)\b", text, re.I))


def check(ans: Answer, *, gold_ids: Sequence[str], answerable: bool, needs_inference: bool) -> dict[str, bool]:
    """Code checks: refusal when it should; citations exist; the gold events are cited; inference is named."""
    if not answerable:
        return {"ok": ans.refused}
    cites_gold = all(g in ans.cited for g in gold_ids)
    ok = (not ans.refused and not ans.unknown and cites_gold
          and (mentions_inference(ans.text) or not needs_inference))
    return {"ok": ok, "refused": ans.refused, "unknown_ids": bool(ans.unknown), "cites_gold": cites_gold,
            "names_inference": mentions_inference(ans.text)}
