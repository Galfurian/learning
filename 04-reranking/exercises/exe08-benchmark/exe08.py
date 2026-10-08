"""EXE08 — a solved benchmark on the holdout. Nothing to write.

A  embedding                  -> top 3 -> generator
B  embedding -> tev1 (mode A) -> top 3 -> generator
C  embedding -> MiniLM        -> top 3 -> generator
"""

from reranklab.runners import run_benchmark

if __name__ == "__main__":
    run_benchmark(__file__)
