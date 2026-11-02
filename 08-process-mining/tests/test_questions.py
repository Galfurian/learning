import json

from helpers import truth_of, truth_order
from test_recipes import FORBIDDEN

from pmlab.benchmark import DEV, HOLDOUT, LOG_NAMES, TYPES, log_path
from pmlab.events import read_events
from pmlab.evidence import pipeline

FILES = (DEV, HOLDOUT)


def _questions(path):
    return json.loads(path.read_text(encoding="utf-8"))["questions"]


def _ids(name):
    m = pipeline(name)
    return {s for t in m.traces.values() for e in t.entries for s in e.source_ids}


def test_questions_valid():
    seen = set()
    for path in FILES:
        for q in _questions(path):
            assert q["id"] not in seen
            seen.add(q["id"])
            assert q["log"] in LOG_NAMES and log_path(q["log"]).exists()
            assert q["type"] in TYPES
            assert q["order"].startswith("order:") and isinstance(q["now"], (int, float))
            assert isinstance(q["gold_recipe"], (str, list))
            assert all(len(o) == 2 and o[1] in ("running", "unusual") for o in q["gold_open"])
            assert all(len(mv) == 2 and mv[0] in ("log", "model") for mv in q["gold_moves"])
            assert set(q["gold_ids"]) <= _ids(q["log"]), q["id"]
            assert set(q["expect"]) == {"all", "none"}
            for kind in ("all", "none"):
                assert all(isinstance(g, list) and g and all(isinstance(t, str) and t for t in g)
                           for g in q["expect"][kind])
            text = json.dumps(q)
            assert not FORBIDDEN.search(text), q["id"]


def test_dev_types():
    types = [q["type"] for q in _questions(DEV)]
    assert len(types) == 12
    assert {t: types.count(t) for t in set(types)} == {
        "which-recipe": 3, "where": 2, "stopped": 2, "conformance": 2, "normal": 1, "abstain": 2}
    by = {(q["log"], q["now"]): q for q in _questions(DEV) if q["type"] == "stopped"}
    assert ("ref-order", 1118) in by and ("ref-stuck", 1400) in by
    assert any(q["log"] == "ref-prefix" and isinstance(q["gold_recipe"], list) for q in _questions(DEV))


def test_dev_and_holdout_disjoint():
    dev = {(q["log"], q["order"]) for q in _questions(DEV)}
    holdout = {(q["log"], q["order"]) for q in _questions(HOLDOUT)}
    assert len(_questions(HOLDOUT)) == 8
    assert not dev & holdout
    assert {log for log, _ in holdout} == {"holdout", "ref-skip-check", "ref-no-end"}


MOVE_OF = {"skip": "model", "extra": "log"}


def _truth_orders(name):
    if name in ("train", "holdout"):
        return truth_of(name)
    header, _ = read_events(log_path(name))
    return header["orders"]


def test_conformance_gold_matches_the_injected_deviation():
    """Each conformance question: its gold moves are the skip/extra deviations of its truth order."""
    checked = 0
    for path in FILES:
        for q in _questions(path):
            if q["type"] != "conformance":
                continue
            truth = _truth_orders(q["log"])
            owner = {i: oid for oid, o in truth.items() for i in o["event_ids"]}
            trace = pipeline(q["log"]).traces[q["order"]]
            expected = sorted([MOVE_OF[d["kind"]], d["operation"]]
                              for d in truth[truth_order(trace, owner)]["deviations"] if d["kind"] in MOVE_OF)
            assert sorted(q["gold_moves"]) == expected, q["id"]
            checked += 1
    assert checked == 4
