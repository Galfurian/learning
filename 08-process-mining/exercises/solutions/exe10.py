"""EXE10 — the object-centric log. Reference solution."""

from pmlab.log import Entry
from pmlab.ocel import OCEL
from pmlab.ocel import flattening_errors as _flattening_errors
from pmlab.ocel import ocel as _ocel
from pmlab.runners import run_ocel


def ocel(entries: list[Entry]) -> OCEL:
    return _ocel(entries)


def flattening_errors(o: OCEL, object_type: str) -> dict[str, int]:
    return _flattening_errors(o, object_type)


if __name__ == "__main__":
    run_ocel(ocel, flattening_errors, __file__)
