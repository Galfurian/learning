"""EXE08 — performance. Reference solution."""

from pmlab.log import Trace
from pmlab.performance import Stats
from pmlab.performance import performance as _performance
from pmlab.runners import run_performance


def performance(traces: list[Trace]) -> dict[str, Stats]:
    return _performance(traces)


if __name__ == "__main__":
    run_performance(performance, __file__)
