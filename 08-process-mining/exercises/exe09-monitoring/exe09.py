"""EXE09 — online monitoring. Task: see README.md in this folder."""

from pmlab.log import Trace
from pmlab.monitor import Candidates, continuations, known_labels, prefix_fit  # noqa: F401  (for the TODO)
from pmlab.petri import Net
from pmlab.runners import run_candidates


# TODO: which recipes can a running order still be?
# - known = known_labels(nets). prefix_fit(net, trace, known) replays the
#   prefix on one recipe net (cost-0 prefix alignment, open operations
#   checked) and gives a Fit, or None when the recipe no longer fits.
# - recipes: the names (sorted) whose fit is not None.
# - None left: Candidates([], {}, "derived").
# - One left: Candidates([name], {}, "derived", ids). ids: the source ids of
#   the entry after which the count of candidates became one (replay the
#   prefixes entries[:i + 1]; skip the entries whose activity is not known).
# - Two or more: claim "inferred", and the deciding map.
#   continuations(net, fit) gives the sequences that can still follow. An
#   activity that is not in the continuations of every candidate can decide.
#   Per candidate, take those at the lowest index of any sequence; map each to
#   the sorted candidates that have it. Sort the map by activity.
#   Example: after load_board, check_covers -> [gadget], mill_part -> [parts_test].
def candidates(prefix: Trace, nets: dict[str, Net]) -> Candidates:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_candidates(candidates, __file__)
