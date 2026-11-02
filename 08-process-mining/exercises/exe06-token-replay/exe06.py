"""EXE06 — token replay. Task: see README.md in this folder."""

from pmlab.log import Trace
from pmlab.petri import Net
from pmlab.replay import Replay
from pmlab.runners import run_replay


# TODO: replay the complete entries of the trace on the net (the rules of pm4py).
# - Start from net.initial; produced = the tokens of net.initial, consumed = 0.
# - Skip an activity that has no transition with its label (unmapped:*, or an
#   operation of another recipe): no token, no penalty.
# - The transition is not enabled: first fire silent transitions (label None;
#   breadth-first, the shortest sequence) to fill as many of its input places
#   as possible. Their consumed and produced tokens count too. Then add the
#   tokens still missing, count them per place in `missing`, and add
#   (activity, source_ids) to `problems`. Then fire it: count the consumed and
#   the produced tokens.
# - complete=True: at the end, fire silent transitions towards net.final,
#   consume the final marking (missing if absent), and count the tokens left
#   as `remaining`. complete=False (a running case): no final consumption.
# - fitness = 0.5 * (1 - missing / consumed) + 0.5 * (1 - remaining / produced).
def token_replay(net: Net, trace: Trace, *, complete: bool = True) -> Replay:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_replay(token_replay, __file__)
