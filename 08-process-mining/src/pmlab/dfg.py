"""Directly-follows graph. Complete entries only: start entries are ignored."""

from collections import Counter
from dataclasses import dataclass, field

from pmlab.log import Trace


@dataclass
class DFG:
    edges: Counter[tuple[str, str]] = field(default_factory=Counter)
    starts: Counter[str] = field(default_factory=Counter)
    ends: Counter[str] = field(default_factory=Counter)
    times: dict[tuple[str, str], list[float]] = field(default_factory=dict)   # gaps in seconds


def dfg(traces: list[Trace]) -> DFG:
    """Count directly-follows pairs of the complete entries of each trace."""
    d = DFG()
    for trace in traces:
        done = [e for e in trace.entries if e.lifecycle == "complete"]
        if not done:
            continue
        d.starts[done[0].activity] += 1
        d.ends[done[-1].activity] += 1
        for a, b in zip(done, done[1:]):
            edge = (a.activity, b.activity)
            d.edges[edge] += 1
            d.times.setdefault(edge, []).append(b.time - a.time)
    return d


def filter_dfg(d: DFG, min_count: int) -> DFG:
    """Keep edges seen at least min_count times; starts and ends stay."""
    keep = {e for e, c in d.edges.items() if c >= min_count}
    return DFG(
        Counter({e: d.edges[e] for e in keep}),
        Counter(d.starts),
        Counter(d.ends),
        {e: list(t) for e, t in d.times.items() if e in keep},
    )
