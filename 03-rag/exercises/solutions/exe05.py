"""EXE05 — the context, and when to abstain. Task: see README.md in this folder."""

from raglab.context import Context, estimate_tokens, format_chunk
from raglab.index import Hit
from raglab.runners import run_context

# What one error costs your application. Change them to match your use.
COST_MISS = 5.0    # the app refuses, but the manuals had the answer
COST_FALSE = 1.0   # the app passes chunks to the generator for a question the manuals cannot answer

# Any value above 0.325 (d24, no answer) and up to 0.349 (the lowest answerable top-1)
# gives the cheapest row of the table. 0.33 is one of them.
THRESHOLD = 0.33


def build_context(hits: list[Hit], budget: int) -> Context:
    chunks, dropped, seen, used = [], [], set(), 0
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


def answerable(hits: list[Hit]) -> bool:
    return bool(hits) and max(h.score for h in hits) >= THRESHOLD


if __name__ == "__main__":
    run_context(build_context, answerable, __file__, threshold=THRESHOLD, cost_miss=COST_MISS, cost_false=COST_FALSE)
