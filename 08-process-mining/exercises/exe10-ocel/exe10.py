"""EXE10 — the object-centric log. Task: see README.md in this folder."""

from pmlab.log import Entry
from pmlab.ocel import OCEL
from pmlab.runners import run_ocel


# TODO 1: build the object-centric log.
# - Every id in entry.objects and every entry.resource is an object.
# - Its type: "order" for "order:<n>", "pallet" for "pallet:<n>",
#   "resource" for any other id (pmlab.ocel.object_type).
# - The events: all the entries, sorted by (time, number of the first source id).
def ocel(entries: list[Entry]) -> OCEL:
    raise NotImplementedError("You need to implement this function.")


# TODO 2: count the two errors of flattening the log to one case type.
# - Flatten (pmlab.ocel.flatten): one case per object of the type, with every
#   event that references it.
# - "convergence": the number of events that go into two or more cases of
#   the type (count each event once).
# - "divergence": the number of (case, activity) pairs where the case holds
#   two or more complete events of the activity and their other objects
#   differ. Other objects: not of the case type and not resources (orders
#   for pallet cases, pallets for order cases).
def flattening_errors(o: OCEL, object_type: str) -> dict[str, int]:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_ocel(ocel, flattening_errors, __file__)
