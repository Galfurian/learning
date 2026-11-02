"""EXE03 — the directly-follows graph. Task: see README.md in this folder."""

from pmlab.dfg import DFG
from pmlab.log import Trace
from pmlab.runners import run_dfg


# TODO: count the directly-follows pairs of the log.
# - Use only the complete entries of each trace, in their order; skip a trace
#   with none.
# - edges[(a, b)]: how many times b comes directly after a.
# - starts[a] / ends[a]: how many traces start / end with a.
# - times[(a, b)]: the gaps b.time - a.time in seconds, one per pair, in the
#   order you meet them.
def dfg(traces: list[Trace]) -> DFG:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_dfg(dfg, __file__)
