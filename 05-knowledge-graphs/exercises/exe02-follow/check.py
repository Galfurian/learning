from kglab.checks import run_checks
from kglab.graph import Graph, Node


def graph() -> Graph:
    g = Graph()
    for n in ("r1", "r2", "b5", "b1", "t"):
        g.add_node(Node(n, "X"))
    g.add_triple("r1", "serves", "b5", "c1")
    g.add_triple("r2", "serves", "b5", "c1")
    g.add_triple("t", "serves", "b1", "c2")
    g.add_triple("b5", "next", "b1", "c3")
    return g


def checks(exe, check):
    done, out = check.calls(exe.follow, graph(), ["r1"], ["serves"])
    if not done:
        return
    check.ok(out == ["b5"], "one hop forward", out)
    out = exe.follow(graph(), ["b5"], ["^serves"])
    check.ok(out == ["r1", "r2"], "'^' walks backwards; sorted", out)
    out = exe.follow(graph(), ["r1"], ["serves", "next", "^serves"])
    check.ok(out == ["t"], "three hops", out)
    out = exe.follow(graph(), ["r1", "r2"], ["serves"])
    check.ok(out == ["b5"], "no repeats", out)
    check.ok(exe.follow(graph(), ["r1"], ["missing"]) == [], "unknown relation: nothing")
    check.ok(exe.follow(graph(), ["r1"], []) == ["r1"], "empty path: the start nodes")
    check.ok(exe.follow(graph(), [], ["serves"]) == [], "no start: nothing")


run_checks(checks, __file__.replace("check.py", "exe02.py"))
