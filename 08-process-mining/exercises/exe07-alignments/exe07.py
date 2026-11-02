"""EXE07 — alignments. Task: see README.md in this folder."""

from pmlab.align import Alignment
from pmlab.log import Trace
from pmlab.petri import Net
from pmlab.runners import run_align


# TODO: the cheapest alignment of the complete entries of the trace on the net.
# - A state is (marking, position in the trace). From a state:
#   sync  (cost 0): the next entry and an enabled transition with its label;
#   model (cost 1): fire an enabled visible transition, the trace stays;
#   log   (cost 1): take the next entry, the marking stays (also for an
#                   activity with no transition, as unmapped:*);
#   silent (cost 0): fire an enabled transition with label None.
# - Search with Dijkstra (heapq) on (cost, log moves): at equal cost a model
#   move wins over a log move. Expand every state once. Do not enter a
#   marking with more than 3 tokens in one place (pmlab.align.MAX_TOKENS).
# - Goal: complete=True, all entries taken and the marking is net.final;
#   complete=False (a running case), all entries taken, any marking.
# - Return Alignment(cost, moves): the sync, log and model moves in order,
#   each Move(kind, activity, source_ids); a model move has no ids. Silent
#   moves are not in the list.
def align(net: Net, trace: Trace, *, complete: bool = True) -> Alignment:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_align(align, __file__)
