"""EXE05 — write a rule planner. Task: see README.md in this folder."""

from kglab.planner import Plan, Rule, RulePlanner
from kglab.runners import run_plan


# These rules are copied from the scenario contract. They are deliberately
# local to the exercise: the task is to maintain a small, explicit planner.
RULES = [
    Rule("count-serve-bay", r"how many devices serve (?P<x>bay \d+)", ("^serves_bay",), "count"),
    Rule("count-stop", r"how many alarms stop (?P<x>.+?)\?", ("^stops",), "count"),
    Rule("who-serves-bay", r"which devices serve (?P<x>bay \d+)", ("^serves_bay",)),
    Rule("bays-of", r"which bays does (?P<x>.+?) serve", ("serves_bay",)),
    Rule("share-bay", r"from (?P<x>.+?), which devices share", ("serves_bay", "^serves_bay")),
    Rule("same-item", r"handle the kind of item carried by (?P<x>.+?)\?", ("moves", "^moves")),
    Rule("items-of", r"(?:which items can|what can) (?P<x>.+?) (?:move|carry)", ("moves",)),
    Rule("who-moves", r"which devices move (?:a |an |the )?(?P<x>.+?)\?", ("^moves",)),
    Rule("four-hops", r"four route hops from (?P<x>bay \d+)",
         ("next_step", "next_step", "next_step", "next_step")),
    Rule("two-hops", r"follows (?P<x>bay \d+) after two", ("next_step", "next_step")),
    Rule("next-bay", r"follows (?P<x>bay \d+)", ("next_step",)),
    Rule("alarm-stops", r"which alarm stops (?P<x>.+?)\?", ("^stops",)),
    Rule("stopped-by", r"stopped by (?:the )?(?P<x>.+?)\?", ("stops",)),
    Rule("incident-device-vars", r"exposed by the device involved in the (?P<x>.+?)\?",
         ("incident_on", "contains", "exposes_variable")),
    Rule("incident-alarm-device", r"alarm raised in the (?P<x>.+?)\?", ("raised", "^has_alarm")),
    Rule("incident-device", r"which device was named by the (?P<x>.+?)\?", ("incident_on",)),
    Rule("incident-alarm", r"which alarm did .+? report on (?P<x>\d+ \w+)", ("raised",)),
    Rule("confirmed-by-status", r"mission is confirmed by (?:the |a variable in )?(?P<x>.+?)'s",
         ("contains", "exposes_variable", "confirms")),
    Rule("observe-conditions", r"observe the (?P<x>.+?) method conditions",
         ("contains", "exposes_method", "requires", "observed_by")),
    Rule("conditions-vars", r"conditions required by (?P<x>.+?) methods",
         ("exposes_method", "requires", "observed_by")),
    Rule("tells-may-run", r"tells .+? whether (?P<x>\w+) may run", ("requires", "observed_by")),
    Rule("requires", r"which condition does (?P<x>\w+) require", ("requires",)),
    Rule("owner-alarm", r"which device owns the (?P<x>.+?)\?", ("^has_alarm",)),
    Rule("returns", r"what .+? does the (?P<x>.+?) return", ("returns",)),
    Rule("parameters", r"which input names does (?P<x>\w+) accept", ("has_parameter",)),
    Rule("folder-of", r"which folder exposes the (?P<x>.+?)\?", ("^exposes_variable",)),
    Rule("cell-devices", r"which devices belong to the (?P<x>.+?)\?", ("contains",)),
]


def plan(question: str) -> Plan | None:
    return RulePlanner(RULES).plan(question)


if __name__ == "__main__":
    run_plan(plan, __file__)
