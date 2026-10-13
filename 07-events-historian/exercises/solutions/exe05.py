"""EXE05 — product cases. Reference solution."""

from evlab.cases import assign_cases as _assign_cases
from evlab.records import Event
from evlab.runners import run_assign_cases


def assign_cases(events: list[Event]) -> list[Event]:
    return _assign_cases(events)


if __name__ == "__main__":
    run_assign_cases(assign_cases, __file__)
