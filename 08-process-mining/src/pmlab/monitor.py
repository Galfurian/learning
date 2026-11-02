"""Online monitoring: which recipes can a running order still be, and what comes next.

Evidence of a running order at a time `now` (see prefix_at): its complete
entries in order, and its open operations (started, not complete). A start
says "this operation is happening", not "this operation fired": start times
are not reliable for order (a board fetch starts before its pallet is
reserved).

A recipe stays a candidate while
- a prefix alignment of cost 0 of the complete entries exists: they replay
  on the recipe net with sync and silent moves only. The search here (_step)
  is that alignment restricted to cost 0, and it also gives the reached
  markings ("done markings");
- and every open operation can still occur: its label fires on some run from
  a done marking (possibly after other transitions).

Activities that belong to no recipe (`unmapped:*`, or any label with no
transition in any net) are ignored for candidacy. Conformance shows them as
log moves; here they do not tell recipes apart.

One scan over the entries replays the complete entries incrementally per net
and caches the labels reachable from each set of done markings, so the
`deciding_ids` search costs no more replay than the final answer.
"""

from collections import Counter, deque
from dataclasses import dataclass, field

from pmlab.compile import play_out
from pmlab.log import Trace
from pmlab.performance import Open, Stats, open_operations
from pmlab.petri import Net, enabled, fire
from pmlab.recipes import Recipe

Marking = frozenset   # frozenset of (place, tokens) with tokens > 0


@dataclass
class Candidates:
    recipes: list[str]
    deciding: dict[str, list[str]] = field(default_factory=dict)
    claim_kind: str = "inferred"
    deciding_ids: tuple[str, ...] = ()


@dataclass
class Status:
    order: str
    now: float
    candidates: Candidates
    open: list[Open]
    next: list[str]
    remaining_s: float | None


def prefix_at(trace: Trace, now: float) -> Trace:
    """The trace as seen at `now`: the entries with time <= now."""
    return Trace(trace.case_id, [e for e in trace.entries if e.time <= now])


def _key(marking: Counter[str]) -> Marking:
    return frozenset((p, n) for p, n in marking.items() if n > 0)


def _closure(net: Net, markings: set[Marking]) -> set[Marking]:
    """The markings plus every marking reachable from them by silent transitions."""
    out, todo = set(markings), list(markings)
    while todo:
        m = Counter(dict(todo.pop()))
        for t in enabled(net, m):
            if net.transitions[t] is None:
                k = _key(fire(net, m, t))
                if k not in out:
                    out.add(k)
                    todo.append(k)
    return out


def _step(net: Net, markings: set[Marking], label: str) -> set[Marking]:
    """Markings after a sync move on the label from any of the markings, closed
    under silent moves. Empty if the label does not fit."""
    out = set()
    for k in markings:
        m = Counter(dict(k))
        out |= {_key(fire(net, m, t)) for t in enabled(net, m) if net.transitions[t] == label}
    return _closure(net, out)


def _remaining(net: Net, markings: set[Marking]) -> set[tuple[str, ...]]:
    """Visible continuations (play-out bound as compile.play_out) from the markings."""
    out: set[tuple[str, ...]] = set()
    for m in markings:
        out |= play_out(Net(net.places, net.transitions, net.arcs, Counter(dict(m)), net.final))
    return out


def _known(nets: dict[str, Net]) -> set[str]:
    return {lab for net in nets.values() for lab in net.transitions.values() if lab is not None}


def _labels_ahead(net: Net, markings: frozenset[Marking]) -> frozenset[str]:
    """Visible labels that fire on some run from the markings."""
    seen, todo, out = set(markings), list(markings), set()
    while todo:
        m = Counter(dict(todo.pop()))
        for t in enabled(net, m):
            if net.transitions[t] is not None:
                out.add(net.transitions[t])
            k = _key(fire(net, m, t))
            if k not in seen:
                seen.add(k)
                todo.append(k)
    return frozenset(out)


def _advance(net: Net, markings: set[Marking], opens: set[str]) -> set[Marking]:
    """Markings after firing as many open operations as possible (each once, any
    order, silent moves free) from the done markings. States are (marking, set of
    fired opens), each visited once: at most 2 ** len(opens) sets per marking."""
    start = [(m, frozenset()) for m in markings]
    seen, todo = set(start), list(start)
    while todo:
        k, fired = todo.pop()
        m = Counter(dict(k))
        for t in enabled(net, m):
            label = net.transitions[t]
            if label is None:
                nxt = (_key(fire(net, m, t)), fired)
            elif label in opens and label not in fired:
                nxt = (_key(fire(net, m, t)), fired | {label})
            else:
                continue
            if nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    most = max(len(f) for _, f in seen)
    return {k for k, f in seen if len(f) == most}


@dataclass
class Fit:
    done: set[Marking]          # markings after the complete entries
    opens: set[str]             # open operations


def known_labels(nets: dict[str, Net]) -> set[str]:
    """Every visible label of the nets: activities outside it do not tell recipes apart."""
    return _known(nets)


def prefix_fit(net: Net, prefix: Trace, known: set[str]) -> Fit | None:
    """The prefix on one recipe net (EXE09 helper). Replays the complete entries of
    the known activities with sync and silent moves only (a prefix alignment of cost
    0). None if a complete entry does not fit, or an open operation (started, not
    complete) cannot fire on any run from the markings reached."""
    done = _closure(net, {_key(net.initial)})
    pending: dict[str, int] = {}
    for e in prefix.entries:
        if e.activity not in known:
            continue
        if e.lifecycle == "start":
            pending[e.activity] = pending.get(e.activity, 0) + 1
        else:
            pending[e.activity] = max(0, pending.get(e.activity, 0) - 1)
            done = _step(net, done, e.activity)
            if not done:
                return None
    opens = {a for a, c in pending.items() if c > 0}
    if opens and not opens <= _labels_ahead(net, frozenset(done)):
        return None
    return Fit(done, opens)


def continuations(net: Net, fit: Fit) -> set[tuple[str, ...]]:
    """The visible sequences that can still follow (EXE09 helper): from the markings
    of the fit, after the open operations fire, to the end (play-out bound 15)."""
    return _remaining(net, _advance(net, fit.done, fit.opens))


def _scan(prefix: Trace, nets: dict[str, Net]) -> tuple[dict[str, Fit], tuple[str, ...]]:
    """Candidates of the prefix with their done markings, and the source ids of
    the latest entry after which the candidate count became one (empty if the
    count is not one at the end)."""
    known = _known(nets)
    names = sorted(nets)
    done = {n: _closure(nets[n], {_key(nets[n].initial)}) for n in names}
    ahead: dict[tuple[str, frozenset], frozenset[str]] = {}
    pending: dict[str, int] = {}             # open activity -> open starts

    def fitting() -> dict[str, Fit]:
        opens = {a for a, c in pending.items() if c > 0}
        out = {}
        for n in names:
            if not done[n]:
                continue
            key = (n, frozenset(done[n]))
            if opens and key not in ahead:
                ahead[key] = _labels_ahead(nets[n], key[1])
            if not opens or opens <= ahead[key]:
                out[n] = Fit(done[n], opens)
        return out

    current = fitting()
    ids: tuple[str, ...] = ()
    for e in prefix.entries:
        if e.activity not in known:
            continue
        if e.lifecycle == "start":
            pending[e.activity] = pending.get(e.activity, 0) + 1
        else:
            pending[e.activity] = max(0, pending.get(e.activity, 0) - 1)
            for n in names:
                if done[n]:
                    done[n] = _step(nets[n], done[n], e.activity)
        before, current = len(current), fitting()
        if len(current) == 1 and before != 1:
            ids = e.source_ids
    return current, ids if len(current) == 1 else ()


def _deciding(nets: dict[str, Net], fits: dict[str, Fit]) -> dict[str, list[str]]:
    rest = {n: _remaining(nets[n], _advance(nets[n], f.done, f.opens)) for n, f in fits.items()}
    seen = {n: {a for seq in seqs for a in seq} for n, seqs in rest.items()}
    common = set.intersection(*seen.values())
    deciding: dict[str, list[str]] = {}
    for seqs in rest.values():
        dist: dict[str, int] = {}
        for seq in seqs:
            for i, a in enumerate(seq):
                if a not in common and i < dist.get(a, len(seq) + 1):
                    dist[a] = i
        low = min(dist.values(), default=None)
        for a, d in dist.items():
            if d == low:
                deciding[a] = sorted(n for n in fits if a in seen[n])
    return dict(sorted(deciding.items()))


def _candidates(prefix: Trace, nets: dict[str, Net]) -> tuple[Candidates, dict[str, Fit]]:
    fits, ids = _scan(prefix, nets)
    recipes = list(fits)
    if len(recipes) == 1:
        return Candidates(recipes, {}, "derived", ids), fits
    if not recipes:
        return Candidates([], {}, "derived"), fits
    return Candidates(recipes, _deciding(nets, fits), "inferred"), fits


def candidates(prefix: Trace, nets: dict[str, Net]) -> Candidates:
    """Recipes that the running order can still be (see the module docstring).

    `deciding` (ruling R4): the earliest activities, at any distance ahead,
    that occur in the continuations of some but not all candidates, mapped to
    the candidates whose continuations contain them. Continuations: play_out
    of each candidate net from the done markings, advanced by firing as many
    open operations as possible (_advance). The distance of an activity in a
    candidate is the lowest index of its first occurrence over the
    continuations. Per candidate, the activities not shared by every
    candidate with the lowest distance are deciding. Example: after
    reserve_pallet and load_board with load_covers open, gadget can do
    check_covers at once but buffer_board only after test_board, so
    check_covers decides and buffer_board does not. Empty when one recipe or
    none is left.

    `deciding_ids`: the source ids of the entry after which only one recipe
    was left; empty while undecided.

    `claim_kind`: "inferred" with more than one recipe, else "derived" (also
    when no recipe fits: the empty list is a derived fact).
    """
    return _candidates(prefix, nets)[0]


def _shortest(net: Net, markings: set[Marking]) -> list[str] | None:
    """Visible labels on a shortest run (by visible transitions) from the markings
    to the final marking; silent transitions are free. None if unreachable."""
    final = _key(net.final)
    dist = {m: 0 for m in markings}
    parent: dict[Marking, tuple[Marking, str | None] | None] = {m: None for m in markings}
    queue = deque(sorted(markings, key=sorted))
    done: set[Marking] = set()
    while queue:
        k = queue.popleft()
        if k in done:
            continue
        done.add(k)
        if k == final:
            labels = []
            while parent[k] is not None:
                k, label = parent[k]
                if label is not None:
                    labels.append(label)
            return labels[::-1]
        m = Counter(dict(k))
        for t in enabled(net, m):
            label = net.transitions[t]
            nk = _key(fire(net, m, t))
            nd = dist[k] + (label is not None)
            if nk in dist and dist[nk] <= nd:
                continue
            dist[nk] = nd
            parent[nk] = (k, label)
            if label is None:
                queue.appendleft(nk)
            else:
                queue.append(nk)
    return None


def _any_recipe(recipes: dict[str, Recipe]) -> Recipe:
    """One recipe with every operation once (ruling R2: same name, same durations)."""
    ops = {}
    for r in recipes.values():
        for op in r.operations:
            ops.setdefault(op.name, op)
    return Recipe("any", tuple(ops.values()))


def status(trace: Trace, now: float, nets: dict[str, Net], recipes: dict[str, Recipe],
           stats: dict[str, Stats]) -> Status:
    """State of a running order at `now`.

    `open`: operations started and not complete (performance.open_operations).
    `next`: visible labels enabled, after silent moves, at the done markings
    (complete entries only), without the open operations (they run already).
    While undecided, the union over the candidates.
    `remaining_s`: once one recipe is left, the sum of the p50 service times
    (nominal_s when an operation has no stats) of the operations on the
    shortest completion from the done markings, so the open operations count
    in full. Concurrency and waiting are not in the sum. None while undecided
    or when no recipe fits.
    """
    prefix = prefix_at(trace, now)
    cands, fits = _candidates(prefix, nets)
    recipe = recipes[cands.recipes[0]] if len(cands.recipes) == 1 else _any_recipe(recipes)
    running = open_operations(prefix, now, stats, recipe)
    busy = {o.activity for o in running}

    nxt: set[str | None] = set()
    for name, fit in fits.items():
        for k in fit.done:
            nxt |= {nets[name].transitions[t] for t in enabled(nets[name], Counter(dict(k)))}
    nxt.discard(None)

    remaining = None
    if len(cands.recipes) == 1:
        (name,) = cands.recipes
        path = _shortest(nets[name], fits[name].done)
        if path is not None:
            nominal = {op.name: op.nominal_s for op in recipe.operations}
            remaining = sum(stats[a].p50 if a in stats else nominal[a] for a in path)
    return Status(trace.case_id, now, cands, running, sorted(nxt - busy), remaining)
