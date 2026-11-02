from pmlab.checks import run_checks
from pmlab.compile import compile_recipe
from pmlab.log import Entry, Trace
from pmlab.recipes import load_recipes

NETS = {name: compile_recipe(r) for name, r in load_recipes().items()}


def prefix(*ops):
    """ops: (activity, "start" | "complete", time)."""
    return Trace("order:1", [Entry("order:1", a, lc, float(t), "r", ("order:1",), (f"e{i}",), "inferred")
                             for i, (a, lc, t) in enumerate(ops, 1)])


SHARED = (("reserve_pallet", "start", 0), ("reserve_pallet", "complete", 10),
          ("load_board", "start", 12), ("load_board", "complete", 100))


def checks(exe, check):
    done, c = check.calls(exe.candidates, prefix(), NETS)
    if not done:
        return
    check.ok(c.recipes == ["brick_demo", "gadget", "parts_test"] and c.claim_kind == "inferred",
             "an empty order can be any recipe (inferred)", c)
    c = exe.candidates(prefix(*SHARED), NETS)
    check.ok(c.recipes == ["gadget", "parts_test"] and c.claim_kind == "inferred" and c.deciding_ids == (),
             "on the shared prefix: gadget or parts_test, not decided", c)
    check.ok(c.deciding.get("check_covers") == ["gadget"] and c.deciding.get("mill_part") == ["parts_test"],
             "the next bay decides: check_covers for gadget, mill_part for parts_test", c.deciding)
    c = exe.candidates(prefix(*SHARED, ("load_covers", "complete", 200), ("check_covers", "start", 210)), NETS)
    check.ok(c.recipes == ["gadget"] and c.claim_kind == "derived" and c.deciding_ids == ("e6",),
             "a check_covers start decides gadget, with its event id", c)
    c = exe.candidates(prefix(("reserve_pallet", "complete", 10), ("load_bricks", "complete", 50)), NETS)
    check.ok(c.recipes == ["brick_demo"] and c.deciding_ids == ("e2",), "brick_demo diverges at the load step", c)
    c = exe.candidates(prefix(*SHARED, ("unmapped:mission", "complete", 101)), NETS)
    check.ok(c.recipes == ["gadget", "parts_test"], "an unmapped activity does not tell recipes apart", c)
    c = exe.candidates(prefix(("reserve_pallet", "complete", 10), ("assemble_gadget", "complete", 50)), NETS)
    check.ok(c.recipes == [] and c.claim_kind == "derived", "no recipe fits: an empty list, derived", c)


run_checks(checks, __file__.replace("check.py", "exe09.py"))
