"""EXE02 — follow a relation path. Task: see README.md in this folder."""

from collections.abc import Iterable, Sequence

from kglab.graph import Graph
from kglab.runners import run_follow


# TODO: follow `relations` in order, starting from the `start` nodes.
# - graph.neighbors(node, relation) gives the nodes one edge away (subject -> object);
# - graph.neighbors(node, relation, backward=True) walks the edge from object to subject;
# - a relation written "^name" means: follow "name" backwards;
# - after each relation, the frontier is the set of nodes reached (no repeats);
# - return the final frontier as a sorted list; [] if nothing is reached.
def follow(graph: Graph, start: Iterable[str], relations: Sequence[str]) -> list[str]:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_follow(follow, __file__)
