"""EXE06 — a grounded answer, checked by code. Task: see README.md in this folder."""

from raglab.generation import REFUSAL, CitationReport, cited_ids
from raglab.runners import run_rag

SYSTEM_PROMPT = f"""You answer questions about machine manuals.
Use only the manual excerpts in the user message. Each excerpt starts with its id in square brackets.
After every sentence that uses an excerpt, write the excerpt id in square brackets, for example [lx40-cooling-1].
If the excerpts do not contain the answer, reply exactly: {REFUSAL}
Do not use any other knowledge."""


def check_citations(answer: str, context_ids: list[str]) -> CitationReport:
    cited = cited_ids(answer)
    unknown = [c for c in cited if c not in context_ids]
    refused = REFUSAL.lower().rstrip(".") in answer.lower()
    if refused:
        problem = "refusal with citations" if cited else ""
    elif not cited:
        problem = "no citations"
    elif unknown:
        problem = "cites ids that are not in the context: " + ", ".join(unknown)
    else:
        problem = ""
    return CitationReport(cited, unknown, refused, problem == "", problem)


if __name__ == "__main__":
    run_rag(__file__, system_prompt=SYSTEM_PROMPT, check=check_citations)
