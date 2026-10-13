"""EXE04 — signals to events. Reference solution."""

from evlab.records import Change, Event
from evlab.rules import RULES_VERSION
from evlab.runners import run_derive


def derive_missions(changes: list[Change]) -> list[Event]:
    out: list[Event] = []

    def add(activity, c, rule, pallet=None, **attrs):
        out.append(Event(f"e{len(out) + 1}", activity, c.machine, c.event_time, c.event_time_lo, c.event_time_hi,
                         (c.change_id,), rule, RULES_VERSION, "observed", pallet, None, attrs))

    for c in changes:
        field = c.signal.split(".", 1)[1]
        if field == "mission":
            if c.old:
                add("mission_ended", c, "missions", mission=c.old)
            if c.new:
                add("mission_started", c, "missions", mission=c.new)
        elif field.startswith("destination."):
            stop = field.split(".", 1)[1]
            if c.new:
                add("destination_assigned", c, "destinations", pallet=int(c.new), stop=stop)
            elif c.old:
                add("destination_cleared", c, "destinations", pallet=int(c.old), stop=stop)
    return out


if __name__ == "__main__":
    run_derive(derive_missions, __file__)
