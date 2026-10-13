from kglab.builder import Linker, build
from kglab.corpus import Chunk
from kglab.extract import Extraction, Mention
from kglab.graph import Graph, Node
from kglab.metrics import AMBIGUOUS


def tree() -> Graph:
    g = Graph()
    g.add_node(Node("rover1", "Device", "Rover R-1", ["R-1", "first rover"]))
    g.add_node(Node("rover2", "Device", "Rover R-2", ["R-2"]))
    for d in ("rover1", "rover2"):
        g.add_node(Node(f"{d}/Status/Busy", "Variable", "Busy"))
        g.add_node(Node(f"{d}/Motion/StartMission", "Method", "StartMission"))
    return g


GLOSSARY = [Node("bay:5", "Bay", "Bay 5"), Node("cond:rover1/idle", "Condition", "R-1 idle", ["rover R-1 is idle"])]


def test_scoped_resolution_uses_mention_then_chunk():
    linker = Linker(tree())
    assert linker.resolve("the Busy flag of R-2", ("Variable",)).node == "rover2/Status/Busy"
    r = linker.resolve("Busy", ("Variable",), "R-1 waits. Then it reads Busy.")
    assert (r.node, r.level) == ("rover1/Status/Busy", "scoped")
    r = linker.resolve("Busy", ("Variable",), "No device named here.")
    assert r.node == AMBIGUOUS and r.candidates == ("rover1/Status/Busy", "rover2/Status/Busy")


def test_build_keeps_resolved_links_only():
    chunk = Chunk("c1", "c1", "Rovers", "Missions", "R-1 serves bay 5. StartMission needs R-1 idle.")
    ex = Extraction([
        Mention("R-1", "serves_bay", "bay 5"),
        Mention("StartMission", "requires", "R-1 idle"),
        Mention("the crane", "serves_bay", "bay 5"),
    ])
    g, report = build(tree(), GLOSSARY, [chunk], {"c1": ex})
    links = {(e.s, e.r, e.o) for e in g.edges if e.source == "c1"}
    assert links == {("rover1", "serves_bay", "bay:5"), ("rover1/Motion/StartMission", "requires", "cond:rover1/idle")}
    assert report.kept == 2 and report.unresolved["none"] == 1


def test_bare_type_word_means_the_one_in_the_chunk():
    g = tree()
    g.add_node(Node("incident:2026-03-04-1", "Incident", "4 March incident", ["4 March"]))
    g.add_node(Node("incident:2026-03-05-1", "Incident", "5 March incident", ["5 March"]))
    r = Linker(g).resolve("The incident", ("Incident",), "On 4 March, R-1 stopped.")
    assert (r.node, r.level) == ("incident:2026-03-04-1", "chunk")
    assert Linker(g).resolve("The incident", ("Incident",), "R-1 stopped.").node is None


def test_backwards_triple_is_repaired_by_the_types():
    chunk = Chunk("c1", "c1", "Rovers", "Missions", "R-1 serves bay 5.")
    g, report = build(tree(), GLOSSARY, [chunk], {"c1": Extraction([Mention("bay 5", "serves_bay", "R-1")])})
    assert ("rover1", "serves_bay", "bay:5") in g.triples() and report.reversed == 1
