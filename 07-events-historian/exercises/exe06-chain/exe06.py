"""EXE06 — evidence chain. Task: see README.md in this folder."""

from evlab.chain import Chain
from evlab.records import Event
from evlab.runners import run_chain


# TODO: build a Chain for one pallet#cycle.
# Keep only the events with the requested case id, in event-time order.
# Separate destination visits from ordinary steps. A visit is corroborated
# only when loop evidence shows that the pallet left the loop while assigned.
# Keep inferred claims and add a coverage note. Unknown cases must abstain
# with no steps and a "no event" coverage note.
def chain(events: list[Event], case_id: str) -> Chain:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_chain(chain, __file__)
