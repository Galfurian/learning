"""Hits -> the context: the text the generator reads, under a token budget.

The app estimates tokens as len(text) / 4. Ollama reports the real count
after the request (prompt_eval_count); the UI shows both.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field

from .corpus import Chunk
from .index import Hit

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
