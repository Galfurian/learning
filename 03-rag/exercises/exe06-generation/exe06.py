"""EXE06 — a grounded answer, checked by code. Task: see README.md in this folder."""

from raglab.generation import REFUSAL, CitationReport, cited_ids
from raglab.runners import run_rag

# TODO: write the rules the generator must follow:
# - use only the excerpts in the user message;
# - cite the id of every excerpt it uses, in square brackets, e.g. [lx40-cooling-1];
# - when the excerpts do not contain the answer, reply exactly REFUSAL.
SYSTEM_PROMPT = """You answer questions about machine manuals.
"""


# TODO: return CitationReport(cited, unknown, refused, ok, problem):
# - cited: cited_ids(answer)
# - unknown: the cited ids that are not in context_ids
# - refused: REFUSAL (without its final ".") appears in the answer, case-insensitive
# - problem: "" when the answer is fine, else one of
#     "refusal with citations", "no citations", "cites ids that are not in the context: <ids>"
# - ok: problem == ""
def check_citations(answer: str, context_ids: list[str]) -> CitationReport:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_rag(__file__, system_prompt=SYSTEM_PROMPT, check=check_citations)
