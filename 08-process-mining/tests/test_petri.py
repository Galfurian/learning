from collections import Counter

import pytest

from pmlab.petri import Net, enabled, fire


def _net() -> Net:
    return Net(
        places={"i", "p", "o"},
        transitions={"a": "a", "b": "b"},
        arcs={("i", "a"), ("a", "p"), ("p", "b"), ("b", "o")},
        initial=Counter({"i": 1}),
        final=Counter({"o": 1}),
    )


def test_enabled_and_fire():
    net = _net()
    m = Counter(net.initial)
    assert enabled(net, m) == ["a"]
    m = fire(net, m, "a")
    assert m == Counter({"p": 1})
    assert enabled(net, m) == ["b"]
    assert +fire(net, m, "b") == net.final


def test_fire_not_enabled():
    net = _net()
    with pytest.raises(ValueError):
        fire(net, Counter(net.initial), "b")


def test_fire_does_not_change_input():
    net = _net()
    m = Counter(net.initial)
    fire(net, m, "a")
    assert m == Counter({"i": 1})
