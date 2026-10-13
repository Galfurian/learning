"""EXE03 — what is a change. Task: see README.md in this folder."""

from evlab.records import Change
from evlab.rules import CleanReport
from evlab.runners import run_clean


# TODO: keep the changes that change something, in arrival order (sort by change.arrival_seq).
# - the first value of a signal is its initial state, not an event: count it as "initial value";
# - a value equal to the last kept value of that signal is not a change: count "unchanged or duplicate";
# - when change.replay_cycle differs from the previous change's, the simulator restarted: forget the last
#   values, so the next value of each signal is initial again.
# Return (kept changes, CleanReport) with report.dropped[reason] counts and report.kept = len(kept).
def clean(changes: list[Change]) -> tuple[list[Change], CleanReport]:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_clean(clean, __file__)
