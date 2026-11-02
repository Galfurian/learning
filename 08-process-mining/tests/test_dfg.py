import pm4py
from helpers import entries_of, to_pm4py_log

from pmlab.dfg import dfg, filter_dfg
from pmlab.log import to_log


def test_dfg_matches_pm4py():
    traces = to_log(entries_of("train"), "order")
    d = dfg(traces)
    ref, _, _ = pm4py.discover_dfg(to_pm4py_log(traces))
    assert dict(d.edges) == dict(ref)
    assert sum(d.starts.values()) == len(traces) == sum(d.ends.values())
    assert all(len(v) == d.edges[k] for k, v in d.times.items())


def test_filter_dfg():
    d = dfg(to_log(entries_of("train")))
    f = filter_dfg(d, 3)
    assert f.edges and all(c >= 3 for c in f.edges.values())
    assert set(f.times) == set(f.edges)
    assert len(f.edges) <= len(d.edges)
