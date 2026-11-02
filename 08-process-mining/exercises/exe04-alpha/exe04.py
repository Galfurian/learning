"""EXE04 — the Alpha miner. Task: see README.md in this folder."""

from pmlab.log import Trace
from pmlab.petri import Net
from pmlab.runners import run_alpha


# TODO: discover a Petri net with the classic Alpha algorithm.
# 1. Footprint over the activities of the traces (complete entries,
#    trace.activities): a > b when b comes directly after a somewhere.
#    a -> b: a > b and not b > a;  a || b: both;  a # b: neither.
# 2. Pairs (A, B) of activity sets: every a in A -> every b in B, a1 # a2
#    inside A, b1 # b2 inside B. Keep the maximal pairs only.
# 3. One place per maximal pair, named "p(<A sorted, comma>|<B sorted, comma>)",
#    with arcs a -> place for a in A and place -> b for b in B.
# 4. Place "i" before every first activity, place "o" after every last one.
# 5. Transitions: one per activity, id = label = the activity name.
#    initial = Counter({"i": 1}), final = Counter({"o": 1}).
# (pmlab.alpha.footprint is there if you want to start from step 2.)
def alpha(traces: list[Trace]) -> Net:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_alpha(alpha, __file__)
