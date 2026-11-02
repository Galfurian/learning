"""EXE08 — performance. Task: see README.md in this folder."""

from pmlab.log import Trace
from pmlab.performance import Stats
from pmlab.runners import run_performance


# TODO: the service and waiting times of each operation over the traces.
# - In each trace, pair each start entry with the next complete entry of the
#   same activity. A start with no complete is no sample (still running).
# - service = complete.time - start.time.
# - waiting = start.time - the latest complete, in the same trace and at or
#   before the start, of the operation's dependencies (the recipe "depends";
#   the recipe of a case is not known: take the operation by name over all
#   recipes, pmlab.abstraction.operations_by_name). No such complete: no
#   waiting sample.
# - Stats(count of service samples, p50, p95, max of the service times,
#   p50 and p95 of the waiting times). Percentiles: nearest rank,
#   sorted(values)[max(1, ceil(q * n)) - 1]; math.nan when there is no value.
def performance(traces: list[Trace]) -> dict[str, Stats]:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_performance(performance, __file__)
