from kglab.checks import run_checks
from kglab.extract import LINK_RELATIONS

REL = next(iter(LINK_RELATIONS))


def checks(exe, check):
    raw = ('{"triples": [{"subject": " R-1 ", "relation": "%s", "object": "bay 5"},'
           '{"subject": "R-1", "relation": "drives_to", "object": "bay 5"},'
           '{"subject": "", "relation": "%s", "object": "x"}, "text"]}' % (REL, REL))
    done, out = check.calls(exe.parse_triples, raw)
    if not done:
        return
    valid, invalid = out
    check.ok([(m.subject, m.relation, m.object) for m in valid] == [("R-1", REL, "bay 5")],
             "one valid mention, stripped", valid)
    errors = [i.get("error") for i in invalid]
    check.ok(errors == ["relation not in schema", "missing field", "missing field"],
             "invalid items are counted with their reason", errors)
    valid, invalid = exe.parse_triples('Sure: {"triples": []} done')
    check.ok(valid == [] and invalid == [], "JSON inside other text")
    valid, invalid = exe.parse_triples("no json at all")
    check.ok(valid == [] and invalid and invalid[0].get("error") == "no JSON object", "no JSON: one invalid item", invalid)
    valid, invalid = exe.parse_triples('{"other": 1}')
    check.ok(valid == [] and invalid == [], "no triples key: nothing")


run_checks(checks, __file__.replace("check.py", "exe03.py"))
