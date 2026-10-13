from kglab.evalset import GoldPath, Question
from kglab.generation import REFUSAL, check_citations, cited_ids, facts_context, score_answer
from kglab.graph import Graph, Node


def graph() -> Graph:
    g = Graph()
    g.add_node(Node("rover1", "Device", "Rover R-1", ["R-1"]))
    g.add_node(Node("rover2", "Device", "Rover R-2", ["R-2"]))
    g.add_node(Node("bay:5", "Bay", "Bay 5"))
    g.add_triple("rover1", "serves_bay", "bay:5", "rovers-missions")
    g.add_triple("rover2", "serves_bay", "bay:5", "rovers-missions")
    return g


def q(answers, count=None, kind="aggregation") -> Question:
    return Question("t1", "Which rovers serve bay 5?", kind, GoldPath(("bay:5",), ("^serves_bay",)), tuple(answers), count)


def test_facts_context_numbers_and_sources():
    g = graph()
    ctx = facts_context(g, g.edges + g.edges[:1])
    assert ctx.ids == ["f1", "f2"]
    assert ctx.text.splitlines()[0] == "[f1] Rover R-1 serves Bay 5"
    assert ctx.sources == {"f1": "rovers-missions", "f2": "rovers-missions"}


def test_citations():
    assert cited_ids("R-1 [F1]. Also [rovers-missions; f2]") == ["f1", "rovers-missions", "f2"]
    assert check_citations("R-1 [f1] [f9].", ["f1", "f2"]).unknown == ["f9"]
    assert check_citations(REFUSAL, []).ok


def test_score_answer():
    g = graph()
    assert score_answer("R-1 and Rover R-2 [f1][f2].", q(["rover1", "rover2"]), g).ok
    s = score_answer("Only R-1 [f1].", q(["rover1", "rover2"]), g)
    assert s.missing == ["rover2"] and not s.ok
    s = score_answer("R-1 and R-2.", q(["rover1"]), g)
    assert s.extra == ["rover2"] and not s.ok
    assert score_answer("Two rovers: R-1 and R-2.", q(["rover1", "rover2"], count=2), g).ok
    no = Question("t2", "?", "no-answer", None, ())
    assert score_answer(REFUSAL, no, g).ok and not score_answer("R-1.", no, g).ok
