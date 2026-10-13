from kglab.graph import Graph, Node, follow, follow_edges, from_json, to_json


def small() -> Graph:
    g = Graph()
    for n in ("rover1", "rover2", "bay:5", "bay:1", "cell:test"):
        g.add_node(Node(n, "Device"))
    g.add_triple("rover1", "serves_bay", "bay:5", "c1")
    g.add_triple("rover2", "serves_bay", "bay:5", "c1")
    g.add_triple("cell:test", "serves_bay", "bay:1", "c2")
    g.add_triple("bay:5", "next_step", "bay:1", "c3")
    return g


def test_duplicate_triple_is_kept_once():
    g = small()
    assert not g.add_triple("rover1", "serves_bay", "bay:5", "other")
    assert len(g.edges) == 4


def test_follow_forward_and_backward():
    g = small()
    assert follow(g, ["rover1"], ["serves_bay"]) == ["bay:5"]
    assert follow(g, ["bay:5"], ["^serves_bay"]) == ["rover1", "rover2"]
    assert follow(g, ["rover1"], ["serves_bay", "next_step", "^serves_bay"]) == ["cell:test"]
    assert follow(g, ["rover1"], ["missing"]) == []


def test_follow_edges_keeps_sources():
    g = small()
    sources = [e.source for e in follow_edges(g, ["rover1"], ["serves_bay", "next_step"])]
    assert sources == ["c1", "c3"]


def test_json_round_trip():
    g = small()
    h = from_json(to_json(g))
    assert h.triples() == g.triples()
    assert set(h.nodes) == set(g.nodes)


def test_follow_edges_drops_dead_branches():
    g = small()
    g.add_triple("rover1", "serves_bay", "bay:9", "c9")   # bay 9 has no next step
    sources = [e.source for e in follow_edges(g, ["rover1"], ["serves_bay", "next_step"])]
    assert sources == ["c1", "c3"]
