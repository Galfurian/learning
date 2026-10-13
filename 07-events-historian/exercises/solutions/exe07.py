"""EXE07 — the answer: the generator reads evidence lines and cites them. Reference solution."""

from evlab.answer import REFUSAL, evidence_lines
from evlab.chain import Chain
from evlab.runners import run_answer

SYSTEM_PROMPT = f"""You answer questions about what happened on a production line.
Use only the evidence lines in the user message. Each line starts with an event id in square brackets.
After every sentence, write the ids of the lines it uses, for example [e12].
A line marked "inferred link to the pallet" is not observed: say "probably" or "inferred" for it.
An assignment that is not corroborated is an intention, not a movement.
A "why" can come only from a line marked "cause"; if no such line explains it, say the recording does not show why.
Write two to four sentences in your own words. Do not copy the lines. Cite only ids that appear in the lines.
If the lines do not answer the question, reply exactly: {REFUSAL}"""


def messages(question: str, chain: Chain | None) -> list[dict[str, str]]:
    body = "\n".join(evidence_lines(chain)) if chain is not None and chain.steps else "(no evidence)"
    return [{"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Evidence:\n{body}\n\nQuestion: {question}"}]


if __name__ == "__main__":
    run_answer(messages, __file__)
