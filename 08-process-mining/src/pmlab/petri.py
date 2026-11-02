"""A small Petri net: places, labelled transitions, arcs, and the token game."""

from collections import Counter
from dataclasses import dataclass


@dataclass
class Net:
    places: set[str]
    transitions: dict[str, str | None]       # id -> label (None = silent)
    arcs: set[tuple[str, str]]               # (place, transition) or (transition, place)
    initial: Counter[str]
    final: Counter[str]


def _pre(net: Net, t: str) -> list[str]:
    return sorted(p for p, x in net.arcs if x == t and p in net.places)


def _post(net: Net, t: str) -> list[str]:
    return sorted(p for x, p in net.arcs if x == t and p in net.places)


def enabled(net: Net, marking: Counter[str]) -> list[str]:
    """Transitions whose input places all hold a token, sorted by id."""
    return sorted(t for t in net.transitions if all(marking[p] > 0 for p in _pre(net, t)))


def fire(net: Net, marking: Counter[str], t: str) -> Counter[str]:
    """Return the marking after firing t. Raise ValueError if t is not enabled."""
    if t not in enabled(net, marking):
        raise ValueError(f"transition not enabled: {t}")
    new = Counter(marking)
    for p in _pre(net, t):
        new[p] -= 1
    for p in _post(net, t):
        new[p] += 1
    return +new
