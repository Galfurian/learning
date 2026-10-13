"""EXE05 — product cases. Task: see README.md in this folder."""

from evlab.records import Event
from evlab.runners import run_assign_cases


# TODO: assign product-cycle case ids and safe pallet correlations.
# - A destination_assigned event to bay5 starts p<number>#1, then increments
#   the cycle when that pallet is loaded at bay5 again.
# - Pallet-bearing events inherit the current case for that pallet.
# - A QC event or a QC robot mission has no pallet in its signal. Correlate it
#   only to one unambiguous bay4 occupancy and mark the result "inferred".
# - Keep an event case-less when the join is missing or ambiguous.
# Preserve event ids, evidence, and observed claims when no join is made.
def assign_cases(events: list[Event]) -> list[Event]:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_assign_cases(assign_cases, __file__)
