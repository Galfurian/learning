from kglab.benchmark import diagnose, missing_gold_edges
from kglab.builder import BuildReport, Linker
from kglab.evalset import GoldPath, Question
from kglab.extract import Mention
from kglab.graph import Graph, Node
from kglab.pipelines import run_graph
from kglab.planner import Rule, RulePlanner


def gold() -> Graph:
    g = Graph()
    g.add_node(Node("rover1", "Device", "Rover R-1", ["R-1"]))
    g.add_node(Node("rover2", "Device", "Rover R-2", ["R-2"]))
    g.add_node(Node("bay:5", "Bay", "Bay 5"))
    g.add_triple("rover1", "serves_bay", "bay:5", "c1")
    g.add_triple("rover2", "serves_bay", "bay:5", "c2")
    return g


Q = Question("q1", "Which devices serve bay 5?", "aggregation", GoldPath(("bay:5",), ("^serves_bay",)), ("rover1", "rover2"))
PLANNER = RulePlanner([Rule("who", r"which devices serve (?P<x>bay \d)", ("^serves_bay",))])


def test_gold_graph_answers_and_diagnoses_none():
    g = gold()
    run = run_graph(Q, g, Linker(g), PLANNER, generator=False)
    assert run.start_ids == ["bay:5"] and run.nodes == ["rover1", "rover2"]
    assert diagnose(run, g, g) == "NONE"


def test_missing_edge_is_extraction_or_resolution():
    g, built = gold(), gold()
    built = Graph()
    for n in g.nodes.values():
        built.add_node(n)
    built.add_triple("rover1", "serves_bay", "bay:5", "c1")
    run = run_graph(Q, built, Linker(built), PLANNER, generator=False)
    assert [e.source for e in missing_gold_edges(Q, g, built)] == ["c2"]
    assert diagnose(run, g, built) == "EXTRACTION"
    report = BuildReport(dropped=[("c2", Mention("the other rover", "serves_bay", "bay 5"), "none")])
    assert diagnose(run, g, built, report) == "RESOLUTION"


def test_plan_then_linking():
    g = gold()
    assert diagnose(run_graph(Q, g, Linker(g), RulePlanner([]), generator=False), g, g) == "PLAN"
    wrong = RulePlanner([Rule("who", r"which devices serve (?P<x>bay \d)", ("serves_bay",))])
    assert diagnose(run_graph(Q, g, Linker(g), wrong, generator=False), g, g) == "PLAN"
    far = RulePlanner([Rule("who", r"which devices serve (?P<x>bay \d)", ("^serves_bay",))])
    q = Question("q2", "Which devices serve bay 7?", "aggregation", GoldPath(("bay:5",), ("^serves_bay",)), ("rover1",))
    assert diagnose(run_graph(q, g, Linker(g), far, generator=False), g, g) == "LINKING"
