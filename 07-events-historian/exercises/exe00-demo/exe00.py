"""EXE00 — a solved demo. Nothing to write: read it, run it, follow one pallet."""

from evlab.runners import run_demo

# value changes (collector) -> real changes (clean) -> events (rules) -> cases (pallet#cycle)
# -> the evidence chain of one case -> causal rules -> the generator's answer, citing event ids

if __name__ == "__main__":
    run_demo(__file__)
