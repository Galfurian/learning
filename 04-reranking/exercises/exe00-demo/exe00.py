"""EXE00 — a solved demo. Nothing to write: read it, run it, compare the stages."""

from reranklab.runners import run_demo

# QUESTION -> FIRST STAGE (nomic-embed-text, 20 candidates)
#          -> RERANKER (MiniLM cross-encoder, reads question + candidate)
#          -> top 3 -> GENERATIVE MODEL
# The reranker can only reorder the 20 candidates the first stage found.

if __name__ == "__main__":
    run_demo(__file__)
