"""EXE03 — the directly-follows graph. Reference solution."""

from pmlab.dfg import DFG
from pmlab.dfg import dfg as _dfg
from pmlab.log import Trace
from pmlab.runners import run_dfg


def dfg(traces: list[Trace]) -> DFG:
    return _dfg(traces)


if __name__ == "__main__":
    run_dfg(dfg, __file__)
