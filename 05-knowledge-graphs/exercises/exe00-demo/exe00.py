"""EXE00 — a solved demo. Nothing to write: read it, run it, compare the three pipelines."""

from kglab.runners import run_demo

# chunks  QUESTION -> BM25 (20 candidates) -> MiniLM -> top 3 chunks       -> GENERATIVE MODEL
# gold    QUESTION -> plan -> start nodes -> follow the gold graph -> facts -> GENERATIVE MODEL
# built   the same, on the graph built from the data models + the links extracted from the prose
# A graph can only connect the facts that its extraction kept.

if __name__ == "__main__":
    run_demo(__file__)
