from pmlab.abstraction import abstract
from pmlab.checks import run_checks
from pmlab.events import Event
from pmlab.recipes import load_recipes


def ev(i, t, activity, resource, pallet=None, kind="observed", **attrs):
    return Event(f"e{i}", activity, resource, t, pallet, kind, attrs, ())


def mission(i, start, end, resource, name):
    return [ev(i, start, "mission_started", resource, mission=name), ev(i + 1, end, "mission_ended", resource,
                                                                         mission=name)]


EVENTS = [
    *mission(1, 2, 20, "robot_a", "fetch_board_from_storage"),
    *mission(3, 21, 30, "robot_a", "place_board_on_pallet"),
    ev(5, 32, "bay_stay", "conveyor", pallet=7, kind="derived", bay="load", start=5.0, corroborated=True),
    *mission(6, 50, 55, "robot_a", "wave_hello"),
    ev(8, 70, "test_result", "tester", result="pass"),
    ev(9, 80, "bay_stay", "conveyor", pallet=7, kind="derived", bay="tester", start=40.0, corroborated=True),
    ev(10, 90, "mission_started", "robot_b", mission="go_to_qc_bay"),
    ev(11, 99, "mission_started", "robot_a", mission="fetch_cover_top_from_storage"),
]
ORDERS = {f"e{i}": "order:1" for i in range(1, 11)}      # e11 belongs to no order

# Covers loaded, check failed, covers to the bin, covers loaded again: the second load is reload_covers.
COVERS = ["fetch_cover_top_from_storage", "fetch_cover_bottom_from_storage", "place_cover_top_on_pallet",
          "place_cover_bottom_on_pallet"]
BIN = ["take_cover_top_from_pallet", "take_cover_bottom_from_pallet", "go_to_bin", "drop_covers_in_bin", "go_home"]
FAIL = [
    *[e for k, m in enumerate(COVERS) for e in mission(1 + 2 * k, 10 + 10 * k, 15 + 10 * k, "robot_a", m)],
    *mission(9, 60, 65, "robot_b", "go_to_qc_bay"),
    ev(11, 70, "check_failed", "qc_station", kind="derived"),
    ev(32, 75, "bay_stay", "conveyor", pallet=7, kind="derived", bay="qc", start=58.0, corroborated=True),
    *[e for k, m in enumerate(BIN) for e in mission(12 + 2 * k, 80 + 10 * k, 85 + 10 * k, "robot_b", m)],
    *[e for k, m in enumerate(COVERS) for e in mission(22 + 2 * k, 140 + 10 * k, 145 + 10 * k, "robot_a", m)],
    ev(30, 300, "bay_stay", "conveyor", pallet=8, kind="derived", bay="mill", start=250.0, open=True,
       corroborated=True),
    ev(31, 260, "program_started", "mill_cell", kind="derived", program="engrave"),
]
FAIL_ORDERS = {e.event_id: "order:2" for e in FAIL}


def checks(exe, check):
    try:
        out = abstract(EVENTS, load_recipes(), ORDERS, match=exe.match_operations)
    except NotImplementedError:
        check.ok(False, "match_operations() is implemented")
        return
    rows = {(e.activity, e.lifecycle): e for e in out}
    board = rows.get(("load_board", "start")), rows.get(("load_board", "complete"))
    check.ok(all(board) and (board[0].time, board[1].time) == (2, 30),
             "two missions are one load_board: start at the first evidence, complete at the last",
             [(e.time if e else None) for e in board])
    check.ok(board[1] is not None and board[1].source_ids == ("e1", "e2", "e3", "e4"),
             "the entry cites every event it uses", board[1] and board[1].source_ids)
    test = rows.get(("test_board", "complete"))
    check.ok(test is not None and test.source_ids == ("e8", "e9"), "the tester stay and the result are test_board",
             test and test.source_ids)
    check.ok(("unmapped:mission", "complete") in rows, "a mission that matches no step is kept as unmapped:mission",
             sorted(rows))
    check.ok(("check_covers", "start") in rows and ("check_covers", "complete") not in rows,
             "a mission that only started gives a start and no complete")
    check.ok(all("e11" not in e.source_ids for e in out), "an event with no order is left out")
    cited = {i for e in out for i in e.source_ids}
    check.ok(cited == set(ORDERS), "every event of the order is cited", sorted(set(ORDERS) - cited))

    fail = abstract(FAIL, load_recipes(), FAIL_ORDERS, match=exe.match_operations)
    done = [e.activity for e in fail if e.lifecycle == "complete"]
    check.ok(done == ["load_covers", "check_covers", "bin_covers", "reload_covers"],
             "covers loaded after bin_covers are reload_covers, not a second load_covers", done)
    reload = next((e for e in fail if e.activity == "reload_covers"), None)
    check.ok(reload is not None and reload.source_ids[0] == "e22", "reload_covers cites the second covers missions",
             reload and reload.source_ids)
    engrave = [e.lifecycle for e in fail if e.activity == "engrave_gadget"]
    check.ok(engrave == ["start"], "an open mill stay (attrs.open): engrave_gadget starts and does not complete",
             engrave)


run_checks(checks, __file__.replace("check.py", "exe02.py"))
