"""EXE05 — the context, and when to abstain. Task: see README.md in this folder."""

from raglab.context import Context, estimate_tokens, format_chunk
from raglab.index import Hit
from raglab.runners import run_context

# What one error costs your application. Change them to match your use.
COST_MISS = 5.0    # the app refuses, but the manuals had the answer
COST_FALSE = 1.0   # the app passes chunks to the generator for a question the manuals cannot answer

# TODO: after you run this file once, choose a threshold from the table.
THRESHOLD = 0.0


# TODO: build the context from the hits:
# - in rank order (hit.rank), each chunk at most once (same chunk.id);
# - each chunk formatted with format_chunk(chunk), chunks joined by "\n\n";
# - a chunk costs estimate_tokens(format_chunk(chunk)) + 1; when it does not
#   fit in what is left of `budget`, skip it (put it in `dropped`) and try
#   the next one;
# - return Context(chunks, text, estimate_tokens(text), dropped).
def build_context(hits: list[Hit], budget: int) -> Context:
    raise NotImplementedError("You need to implement this function.")


# TODO: True when the APP should pass these hits to the generator:
# the best hit's score is at least THRESHOLD. No hits: False.
def answerable(hits: list[Hit]) -> bool:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_context(build_context, answerable, __file__, threshold=THRESHOLD, cost_miss=COST_MISS, cost_false=COST_FALSE)
