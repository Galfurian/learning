"""EXE01 — the event log and the case notion. Reference solution."""

from pmlab.log import Entry, Trace
from pmlab.log import to_log as _to_log
from pmlab.runners import run_to_log


def to_log(entries: list[Entry], case_notion: str = "order") -> list[Trace]:
    return _to_log(entries, case_notion)


if __name__ == "__main__":
    run_to_log(to_log, __file__)
