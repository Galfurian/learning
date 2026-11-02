"""EXE02 — event abstraction. Task: see README.md in this folder."""

from pmlab.abstraction import Case, Unit, same_record  # noqa: F401  (same_record: for the TODO)
from pmlab.runners import run_abstract


# TODO: for one order, say which operation each low-level unit is evidence of.
# `units` are the order's evidence units in time order (a robot mission is one
# unit: started + ended). Skip the bay stays: pmlab places them after you.
# For every other unit:
# - case.candidates(unit): the (operation, step index) pairs it matches, most
#   specific steps only. None: append the unit to case.unmapped.
# - The fail-branch rule: reload_covers has the same missions as load_covers.
#   A fail operation (case.ops[name].branch == "fail") wins once every operation
#   it depends on has started (case.started(dep, unit.begin)); before that it
#   cannot run, so keep only the main operations.
# - Join the most recent instance (case.latest(name)) of a remaining operation:
#   a copy of a unit it already has (same_record) or one more part of the same
#   cell operation (case.consecutive(inst, unit)) goes into inst.extra; a step
#   index it does not have yet goes into inst.units[index].
# - No instance takes it: start one, name = case.in_context(names),
#   case.new(name).units[first step index of that operation] = unit.
def match_operations(case: Case, units: list[Unit]) -> None:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_abstract(match_operations, __file__)
