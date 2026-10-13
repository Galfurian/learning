"""EXE04 — signals to events. Task: see README.md in this folder."""

from evlab.records import Change, Event
from evlab.rules import RULES_VERSION
from evlab.runners import run_derive


# TODO: two rules over clean changes, in their order.
# 1. missions (rule "missions"): a change of a "<machine>.mission" signal.
#    - old not empty -> Event activity "mission_ended", attrs {"mission": old};
#    - new not empty -> Event activity "mission_started", attrs {"mission": new} (after the end, if both).
# 2. destinations (rule "destinations"): a change of "conveyor.destination.<stop>" (the stop is the text after
#    "destination.", e.g. "bay4_2"); the value is a pallet id, 0 = none.
#    - new not 0 -> "destination_assigned", pallet=new, attrs {"stop": stop};
#    - new 0 and old not 0 -> "destination_cleared", pallet=old, attrs {"stop": stop}.
# Every event: event_id "e1", "e2", ... in order; resource = change.machine; times and bounds from the change;
# evidence = (change.change_id,); rule_version = RULES_VERSION; claim_kind "observed" (one change, read as it is).
def derive_missions(changes: list[Change]) -> list[Event]:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_derive(derive_missions, __file__)
