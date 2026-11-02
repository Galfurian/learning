"""EXE04 — the Alpha miner. Reference solution."""

from pmlab.alpha import alpha as _alpha
from pmlab.log import Trace
from pmlab.petri import Net
from pmlab.runners import run_alpha


def alpha(traces: list[Trace]) -> Net:
    return _alpha(traces)


if __name__ == "__main__":
    run_alpha(alpha, __file__)
