"""Copied from unit 03 (03-rag/src/raglab/context.py and generation.py), merged and trimmed.

A citation that exists is not a citation that supports the claim:
check_citations only proves the first.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field

from .corpus import Chunk
from .index import Hit
from .evalset import Question

DEFAULT_BUDGET = 1500


def estimate_tokens(text: str) -> int:
    return (len(text) + 3) // 4


def format_chunk(chunk: Chunk) -> str:
    return f"[{chunk.id}]\n{chunk.text}"


@dataclass
class Context:
    chunks: list[Chunk]
    text: str
    tokens: int
    dropped: list[Chunk] = field(default_factory=list)

    @property
    def ids(self) -> list[str]:
        return [c.id for c in self.chunks]


def build_context(hits: Sequence[Hit], budget: int = DEFAULT_BUDGET) -> Context:
    chunks: list[Chunk] = []
    dropped: list[Chunk] = []
    seen: set[str] = set()
    used = 0
    for hit in sorted(hits, key=lambda h: h.rank):
        if hit.chunk.id in seen:
            continue
        seen.add(hit.chunk.id)
        cost = estimate_tokens(format_chunk(hit.chunk)) + 1
        if used + cost > budget:
            dropped.append(hit.chunk)
            continue
        chunks.append(hit.chunk)
        used += cost
    text = "\n\n".join(format_chunk(c) for c in chunks)
    return Context(chunks, text, estimate_tokens(text), dropped)


REFUSAL = "Not in the manuals."

SYSTEM_PROMPT = f"""You answer questions about machine manuals.
Use only the manual excerpts in the user message. Each excerpt starts with its id in square brackets.
After every sentence that uses an excerpt, write the excerpt id in square brackets, for example [lx40-cooling-1].
If the excerpts do not contain the answer, reply exactly: {REFUSAL}
Do not use any other knowledge."""

BRACKET = re.compile(r"\[([^\[\]]+)\]")
CHUNK_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*-\d+$")


def build_messages(question: str, context: Context, system_prompt: str = SYSTEM_PROMPT) -> list[dict]:
    excerpts = context.text or "(none)"
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Manual excerpts:\n\n{excerpts}\n\nQuestion: {question}"},
    ]


def cited_ids(answer: str) -> list[str]:
    found: list[str] = []
    for inside in BRACKET.findall(answer):
        for token in re.split(r"[,;\s]+", inside.strip().lower()):
            if CHUNK_ID.match(token) and token not in found:
                found.append(token)
    return found


@dataclass
class CitationReport:
    cited: list[str]
    unknown: list[str]
    refused: bool
    ok: bool
    problem: str


def check_citations(answer: str, context_ids: Sequence[str]) -> CitationReport:
    cited = cited_ids(answer)
    unknown = [c for c in cited if c not in set(context_ids)]
    refused = is_refusal(answer)
    if refused:
        problem = "refusal with citations" if cited else ""
    elif not cited:
        problem = "no citations"
    elif unknown:
        problem = "cites ids that are not in the context: " + ", ".join(unknown)
    else:
        problem = ""
    return CitationReport(cited, unknown, refused, problem == "", problem)


def answer_ok(answer: str, question: Question) -> bool:
    """A check by code, where code can check: the facts are there, or it refuses."""
    refused = is_refusal(answer)
    if not question.answerable:
        return refused
    return not refused and all(needle.lower() in answer.lower() for needle in question.must_contain)


def is_refusal(answer: str) -> bool:
    return REFUSAL.lower().rstrip(".") in answer.lower()
