from kglab.graph import Graph, Node
from kglab.metrics import AMBIGUOUS
from kglab.resolve import Resolver, normalize


def graph() -> Graph:
    g = Graph()
    g.add_node(Node("rover1", "Device", "Rover R-1", ["R-1", "the first rover"]))
    g.add_node(Node("rover2", "Device", "Rover R-2", ["R-2"]))
    g.add_node(Node("bay:3", "Bay", "bay 3"))
    return g


def test_normalize():
    assert normalize("The  First-Rover!") == "first rover"


def test_levels():
    r = Resolver(graph(), ambiguous={"the rover": ["rover1", "rover2"]})
    assert r.resolve("Rover R-1").level == "exact"
    assert r.resolve("rover1").node == "rover1"
    got = r.resolve("first rover")
    assert (got.node, got.level) == ("rover1", "normalized")
    got = r.resolve("The rover")
    assert (got.node, got.candidates) == (AMBIGUOUS, ("rover1", "rover2"))
    assert r.resolve("Bay 3").node == "bay:3"
    assert r.resolve("the crane").node is None


def test_type_filter():
    r = Resolver(graph(), types=("Bay",))
    assert r.resolve("R-1").node is None
