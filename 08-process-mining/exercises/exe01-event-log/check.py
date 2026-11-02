from pmlab.checks import run_checks
from pmlab.log import Entry
from pmlab.reference import pm4py, to_pm4py_log


def en(i, t, activity, case="order:1", pallets=(), resource="robot_a"):
    objects = (case, *(f"pallet:{p}" for p in pallets), resource)
    return Entry(case, activity, "complete", t, resource, objects, (f"e{i}",), "derived")


ENTRIES = [
    en(10, 1.0, "load_board", pallets=(9,)),
    en(2, 2.0, "load_covers", pallets=(7,)),
    en(11, 3.0, "test_board", pallets=(9,), resource="tester"),
    en(9, 3.0, "check_covers", pallets=(7,), resource="qc_station"),
    en(4, 4.0, "assemble_gadget", pallets=(8, 9), resource="assembly_cell"),
    en(5, 5.0, "bin_covers", resource="robot_b"),
    en(6, 2.5, "load_board", case="order:10", pallets=(1,)),
    en(7, 6.0, "test_board", case="order:10", pallets=(1,), resource="tester"),
]


def checks(exe, check):
    done, by_order = check.calls(exe.to_log, ENTRIES, "order")
    if not done:
        return
    check.ok([t.case_id for t in by_order] == ["order:1", "order:10"], "one trace per order, sorted by case id",
             [t.case_id for t in by_order])
    one = by_order[0]
    check.ok([e.source_ids[0] for e in one.entries] == ["e10", "e2", "e9", "e11", "e4", "e5"],
             "entries sort by (time, event id number): e9 before e11 at t=3",
             [e.source_ids[0] for e in one.entries])
    check.ok(sum(len(t.entries) for t in by_order) == len(ENTRIES), "the order notion keeps every entry once")

    _, by_pallet = check.calls(exe.to_log, ENTRIES, "pallet")
    acts = {t.case_id: t.activities for t in by_pallet or []}
    check.ok(acts.get("pallet:9") == ("load_board", "test_board", "assemble_gadget")
             and acts.get("pallet:8") == ("assemble_gadget",),
             "an entry with two pallets is copied into both pallet traces", acts)
    check.ok(not any("bin_covers" in a for a in acts.values()), "an entry with no pallet is in no pallet trace")
    check.ok(list(acts) == ["pallet:1", "pallet:7", "pallet:8", "pallet:9"], "pallet traces sort by case id",
             list(acts))
    try:
        exe.to_log(ENTRIES, "robot")
        check.ok(False, "an unknown case notion raises ValueError")
    except ValueError:
        check.ok(True, "an unknown case notion raises ValueError")

    # pm4py reads the same log: same cases, same activity sequences.
    df = to_pm4py_log(by_order)
    ref = {case: tuple(acts) for case, acts in df.groupby("case:concept:name", sort=False)["concept:name"]}
    check.ok(ref == {t.case_id: t.activities for t in by_order}, "pm4py sees the same traces",
             ref)
    check.ok(len(pm4py.get_variants(df)) == 2, "pm4py counts two variants")


run_checks(checks, __file__.replace("check.py", "exe01.py"))
