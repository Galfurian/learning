"""EXE00 — a solved example. Nothing to write: read it, run it, trace it."""

from raglab.generation import SYSTEM_PROMPT
from raglab.runners import run_rag

# The whole pipeline with the library pieces:
#   manuals -> chunks -> EMBEDDING MODEL -> index        (once, cached)
#   question -> EMBEDDING MODEL -> top k chunks -> context -> GENERATIVE MODEL -> answer
# The APP code is everything except the two models.

if __name__ == "__main__":
    run_rag(__file__, system_prompt=SYSTEM_PROMPT)
