from kglab.planner import Plan, Rule, RulePlanner, parse_plan, valid


def test_rule_planner_first_match_wins():
    p = RulePlanner([
        Rule("count-bay", r"how many devices serve (?P<x>bay \d)", ("^serves_bay",), "count"),
        Rule("who-serves", r"which devices serve (?P<x>bay \d)", ("^serves_bay",)),
    ])
    plan = p.plan("Which devices serve bay 5?")
    assert plan == Plan(("bay 5",), ("^serves_bay",), "list", "who-serves")
    assert p.plan("How many devices serve bay 3?").op == "count"
    assert p.plan("What does the rover carry?") is None


def test_parse_plan_validates():
    assert parse_plan('{"start": ["R-1"], "path": ["serves_bay"], "op": "list"}').path == ("serves_bay",)
    assert parse_plan('{"start": ["R-1"], "path": ["drives_to"], "op": "list"}') is None
    assert parse_plan("nope") is None
    assert not valid(Plan((), ("serves_bay",)))
