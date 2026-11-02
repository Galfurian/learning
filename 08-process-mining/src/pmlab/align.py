"""Alignments: the cheapest way to explain a trace with a run of the net.

An alignment is a list of moves:
- sync: the trace entry and a net transition with the same label move together;
- log: the trace has an entry that the net does not do here (also every
  activity with no transition, as `unmapped:*`);
- model: the net does a visible transition that the trace does not have.

Costs: log move 1, visible model move 1, sync 0, silent transition 0. This is
pm4py's standard cost function divided by 10000 (pm4py: log and model 10000,
silent 1, sync 0), rounded down.

Silent transitions are fired by the search but are not in `moves`: the list
holds only sync, log and visible model moves, so it stays readable.

Search: Dijkstra over states (marking, position in the trace). Only complete
entries count. Every state is expanded once (visited set), so the search ends
also on the loop of a fail branch. A marking with more than MAX_TOKENS tokens
in one place is not entered: the compiled nets are safe (at most one token per
place), so this bound cuts no real run, and the state space is finite:
at most (MAX_TOKENS + 1) ** places * (trace length + 1) states.

Ties at equal cost: the search takes the alignment with fewer log moves, so
a model move wins over a log move (a skipped operation, not an extra entry).
The search orders states by (cost, log moves); the order stays valid for
Dijkstra because every move adds a non-negative pair. Remaining ties:
successors are queued in the order sync, silent, model, log, then by label
(transition id), and states with the same pair leave the queue in the order
they came in.
"""

import heapq
from collections import Counter
from dataclasses import dataclass, field
from itertools import count

from pmlab.log import Entry, Trace
from pmlab.petri import Net

MAX_TOKENS = 3
_RANK = {"sync": 0, "silent": 1, "model": 2, "log": 3}


@dataclass
class Move:
    kind: str                       # "sync" | "log" | "model"
    activity: str
    source_ids: tuple[str, ...] = ()


@dataclass
class Alignment:
    cost: int
    moves: list[Move] = field(default_factory=list)


def _key(marking: Counter[str]) -> frozenset:
    return frozenset((p, n) for p, n in marking.items() if n > 0)


def align(net: Net, trace: Trace, *, complete: bool = True) -> Alignment:
    """Optimal alignment of the complete entries of a trace on a net.

    With complete=True the run must end in the final marking of the net. With
    complete=False (a running case) any marking reached after the last entry
    is a goal: the unfinished part of the run is not a deviation."""
    entries: list[Entry] = [e for e in trace.entries if e.lifecycle == "complete"]
    pre = {t: Counter(p for p, x in net.arcs if x == t and p in net.places) for t in net.transitions}
    post = {t: Counter(p for x, p in net.arcs if x == t and p in net.places) for t in net.transitions}
    order = sorted(net.transitions, key=lambda t: (net.transitions[t] is None, net.transitions[t] or "", t))
    final = _key(net.final)

    start = (_key(net.initial), 0)
    best = {start: (0, 0)}
    parent: dict[tuple, tuple[tuple, str, str, tuple[str, ...]] | None] = {start: None}
    done: set[tuple] = set()
    tick = count()
    queue = [((0, 0), next(tick), start)]

    while queue:
        (cost, logs), _, state = heapq.heappop(queue)
        if state in done:
            continue
        done.add(state)
        mkey, pos = state
        if pos == len(entries) and (not complete or mkey == final):
            return Alignment(cost, _moves(parent, state))
        marking = Counter(dict(mkey))
        entry = entries[pos] if pos < len(entries) else None

        succ = []
        for t in order:
            if any(marking[p] < n for p, n in pre[t].items()):
                continue
            nxt = marking.copy()
            nxt.subtract(pre[t])
            nxt.update(post[t])
            if any(n > MAX_TOKENS for n in nxt.values()):
                continue
            label = net.transitions[t]
            if label is None:
                succ.append(("silent", t, 0, (_key(nxt), pos), ()))
                continue
            if entry is not None and label == entry.activity:
                succ.append(("sync", label, 0, (_key(nxt), pos + 1), entry.source_ids))
            succ.append(("model", label, 1, (_key(nxt), pos), ()))
        if entry is not None:
            succ.append(("log", entry.activity, 1, (mkey, pos + 1), entry.source_ids))
        succ.sort(key=lambda s: (_RANK[s[0]], s[1]))

        for kind, label, step, nstate, ids in succ:
            nkey = (cost + step, logs + (kind == "log"))
            if nstate in done or (nstate in best and best[nstate] <= nkey):
                continue
            best[nstate] = nkey
            parent[nstate] = (state, kind, label, ids)
            heapq.heappush(queue, (nkey, next(tick), nstate))

    raise ValueError(f"no alignment for {trace.case_id}: the goal marking is not reachable")


def _moves(parent: dict, state: tuple) -> list[Move]:
    moves = []
    while parent[state] is not None:
        state, kind, label, ids = parent[state]
        if kind != "silent":
            moves.append(Move(kind, label, ids))
    return moves[::-1]
