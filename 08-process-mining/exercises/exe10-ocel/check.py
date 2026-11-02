import json
import tempfile
from pathlib import Path

from pmlab.checks import run_checks
from pmlab.log import Entry
from pmlab.ocel import to_ocel_json
from pmlab.reference import pm4py


def en(i, t, activity, objects, resource="robot_a", case="order:1"):
    return Entry(case, activity, "complete", t, resource, objects, (f"e{i}",), "inferred")


# order:1 uses pallets 1 and 2; order:2 reuses pallet 1, and checks its covers twice on two pallets.
ENTRIES = [
    en(3, 3.0, "assemble_gadget", ("order:1", "pallet:1", "pallet:2"), "assembly_cell"),
    en(1, 1.0, "load_board", ("order:1", "pallet:1")),
    en(2, 1.0, "load_covers", ("order:1", "pallet:2")),
    en(4, 5.0, "load_board", ("order:2", "pallet:1"), case="order:2"),
    en(5, 6.0, "check_covers", ("order:2", "pallet:1"), "qc_station", case="order:2"),
    en(6, 7.0, "check_covers", ("order:2", "pallet:3"), "qc_station", case="order:2"),
]


def checks(exe, check):
    done, o = check.calls(exe.ocel, ENTRIES)
    if not done:
        return
    check.ok(o.objects.get("order:1") == "order" and o.objects.get("pallet:3") == "pallet"
             and o.objects.get("qc_station") == "resource", "object types: order, pallet, resource",
             o.objects)
    check.ok(all(e.resource in o.objects for e in ENTRIES), "every resource is an object")
    check.ok([e.source_ids[0] for e in o.events] == ["e1", "e2", "e3", "e4", "e5", "e6"],
             "events sort by (time, event id number)", [e.source_ids[0] for e in o.events])

    _, pallet = check.calls(exe.flattening_errors, o, "pallet")
    check.ok(pallet == {"convergence": 1, "divergence": 1},
             "pallet cases: assemble_gadget is copied into two pallets (convergence); pallet:1 loads a board for "
             "two orders (divergence)", pallet)
    _, order = check.calls(exe.flattening_errors, o, "order")
    check.ok(order == {"convergence": 0, "divergence": 1},
             "order cases: no copy; order:2 checks covers twice on two pallets (divergence)", order)

    # pm4py reads your log as OCEL 2.0 JSON.
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "log.jsonocel"
        path.write_text(json.dumps(to_ocel_json(o)), encoding="utf-8")
        got = pm4py.read_ocel2_json(str(path))
    check.ok(len(got.events) == len(ENTRIES) and len(got.objects) == len(o.objects),
             "pm4py reads the same events and objects", (len(got.events), len(got.objects)))


run_checks(checks, __file__.replace("check.py", "exe10.py"))
