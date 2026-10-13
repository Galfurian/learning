"""EXE05 — write a rule planner. Task: see README.md in this folder."""

from kglab.planner import Plan, Rule, RulePlanner
from kglab.runners import run_plan


RULES = [
    Rule("count-serve-bay", r"how many devices serve (?P<x>bay \d+)", ("^serves_bay",), "count"),
    Rule("who-serves-bay", r"which devices serve (?P<x>bay \d+)", ("^serves_bay",)),
    Rule("next-bay", r"follows (?P<x>bay \d+)", ("next_step",)),
]


# TODO: turn a natural-language question into a graph plan.
# - use RulePlanner(RULES), or write equivalent regex rules;
# - the returned Plan has start mentions, a relation path, and op "list" or "count";
# - preserve the case of the mention copied from the question;
# - return None when no rule matches.
def plan(question: str) -> Plan | None:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_plan(plan, __file__)
