"""Classic Alpha miner (no short-loop extension)."""

from collections import Counter
from itertools import combinations

from pmlab.log import Trace
from pmlab.petri import Net


def footprint(traces: list[Trace]) -> dict[tuple[str, str], str]:
    """Footprint relation of each activity pair: "->", "<-", "||" or "#"."""
    follows: set[tuple[str, str]] = set()
    acts: set[str] = set()
    for t in traces:
        a = t.activities
        acts.update(a)
        follows.update(zip(a, a[1:]))
    fp = {}
    for x in acts:
        for y in acts:
            xy, yx = (x, y) in follows, (y, x) in follows
            fp[(x, y)] = "||" if xy and yx else "->" if xy else "<-" if yx else "#"
    return fp


def alpha(traces: list[Trace]) -> Net:
    """Discover a workflow net with the Alpha algorithm. Start place `i`, end place `o`."""
    fp = footprint(traces)
    acts = sorted({a for a, _ in fp})
    starts = {t.activities[0] for t in traces if t.activities}
    ends = {t.activities[-1] for t in traces if t.activities}

    def choice(s: frozenset[str]) -> bool:
        return all(fp[(x, y)] == "#" for x in s for y in s)

    # Grow pairs (A, B) from the single causal pairs until no pair merges.
    pairs = {
        (frozenset([a]), frozenset([b]))
        for a in acts
        for b in acts
        if fp[(a, b)] == "->" and choice(frozenset([a])) and choice(frozenset([b]))
    }
    grown = True
    while grown:
        grown = False
        for (a1, b1), (a2, b2) in combinations(sorted(pairs, key=lambda p: (sorted(p[0]), sorted(p[1]))), 2):
            a, b = a1 | a2, b1 | b2
            if (a, b) in pairs:
                continue
            if choice(a) and choice(b) and all(fp[(x, y)] == "->" for x in a for y in b):
                pairs.add((a, b))
                grown = True
    maximal = {p for p in pairs if not any(p != q and p[0] <= q[0] and p[1] <= q[1] for q in pairs)}

    places = {"i", "o"}
    arcs: set[tuple[str, str]] = {("i", a) for a in starts} | {(a, "o") for a in ends}
    for a_set, b_set in sorted(maximal, key=lambda p: (sorted(p[0]), sorted(p[1]))):
        place = f"p({','.join(sorted(a_set))}|{','.join(sorted(b_set))})"
        places.add(place)
        arcs |= {(a, place) for a in a_set} | {(place, b) for b in b_set}
    return Net(places, {a: a for a in acts}, arcs, Counter({"i": 1}), Counter({"o": 1}))
