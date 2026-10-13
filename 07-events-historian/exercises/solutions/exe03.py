"""EXE03 — what is a change. Reference solution."""

from evlab.records import Change
from evlab.rules import CleanReport
from evlab.runners import run_clean


def clean(changes: list[Change]) -> tuple[list[Change], CleanReport]:
    report, last, cycle, kept = CleanReport(), {}, None, []
    for c in sorted(changes, key=lambda c: c.arrival_seq):
        if cycle is not None and c.replay_cycle != cycle:
            last.clear()
        cycle = c.replay_cycle
        if c.signal not in last:
            last[c.signal] = c.new
            report.dropped["initial value"] += 1
        elif c.new == last[c.signal]:
            report.dropped["unchanged or duplicate"] += 1
        else:
            last[c.signal] = c.new
            kept.append(c)
    report.kept = len(kept)
    return kept, report


if __name__ == "__main__":
    run_clean(clean, __file__)
