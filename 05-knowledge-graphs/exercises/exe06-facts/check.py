from kglab.checks import run_checks
from kglab.generation import estimate_tokens
from kglab.graph import Graph, Node


def graph() -> Graph:
    g = Graph()
    g.add_node(Node("rover1", "Device", "Rover R-1", ["R-1"]))
    g.add_node(Node("rover2", "Device", "Rover R-2", ["R-2"]))
    g.add_node(Node("bay:5", "Bay", "Bay 5"))
    g.add_triple("rover1", "serves_bay", "bay:5", "rovers-missions")
    g.add_triple("rover2", "serves_bay", "bay:5", "rovers-missions")
    return g


def checks(exe, check):
    g = graph()
    done, out = check.calls(exe.facts_context, g, g.edges + g.edges[:1])
    if not done:
        return
    check.ok(out.ids == ["f1", "f2"], "unique facts get consecutive ids", out.ids)
    check.ok(out.text.splitlines() == [
        "[f1] Rover R-1 (rover1) serves_bay Bay 5 (bay:5)",
        "[f2] Rover R-2 (rover2) serves_bay Bay 5 (bay:5)",
    ], "facts use readable labels and relation names", out.text)
    check.ok(out.sources == {"f1": "rovers-missions", "f2": "rovers-missions"},
             "sources point from fact id to edge source", out.sources)
    check.ok(out.tokens == estimate_tokens(out.text), "tokens describe the context text", out.tokens)
    tiny = exe.facts_context(g, g.edges, budget=1)
    check.ok(tiny.ids == [] and tiny.dropped == 2, "budget drops facts that do not fit", (tiny.ids, tiny.dropped))


run_checks(checks, __file__.replace("check.py", "exe06.py"))
