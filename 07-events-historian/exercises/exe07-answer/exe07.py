"""EXE07 — the answer: the generator reads evidence lines and cites them. Task: see README.md in this folder."""

from evlab.answer import REFUSAL
from evlab.chain import Chain
from evlab.runners import run_answer

# TODO: write the system prompt. The generator must:
# - use only the evidence lines; cite the ids in square brackets after every sentence, for example [e12];
# - say "inferred" or "probably" for a line marked "inferred link to the pallet";
# - treat an assignment that is not corroborated as an intention, not a movement;
# - give a "why" only from a line marked "cause", else say the recording does not show why;
# - refuse with exactly REFUSAL when the lines do not answer.
SYSTEM_PROMPT = ""


# TODO: the messages for one question: the system prompt, then one user message with
# "Evidence:", the evidence lines (one per line; "(no evidence)" if the chain is None or empty), and the question.
# The evidence lines are evlab.answer.evidence_lines(chain).
def messages(question: str, chain: Chain | None) -> list[dict[str, str]]:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_answer(messages, __file__)
