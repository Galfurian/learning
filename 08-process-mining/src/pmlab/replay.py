"""Token replay: play a trace on a net, count missing and remaining tokens.

Rules (the same as pm4py token-based replay):
- Only complete entries are replayed, in order.
- An activity with no transition in the net (`unmapped:*`, or the operation of
  another recipe) is skipped: it adds no token and no penalty, as in pm4py.
- When the next transition is not enabled, first fire silent transitions to
  fill as many of its input places as possible (shortest sequence); their
  tokens count as consumed and produced. Then add the tokens still missing
  and count them.
- Produced and consumed tokens include the initial token and the final
  consumption. At the end of a complete trace, silent transitions first move
  the marking toward the final marking; then the final marking is consumed and
  the tokens left over count as remaining.
- Fitness = 0.5 * (1 - missing / consumed) + 0.5 * (1 - remaining / produced).
"""

from collections import Counter, deque
from dataclasses import dataclass, field

from pmlab.log import Trace
from pmlab.petri import Net, enabled, fire

MAX_SILENT_STATES = 2000


@dataclass
class Replay:
    fitness: float
    produced: int
    consumed: int
    missing: Counter[str] = field(default_factory=Counter)
    remaining: Counter[str] = field(default_factory=Counter)
    problems: list[tuple[str, tuple[str, ...]]] = field(default_factory=list)


def _pre(net: Net, t: str) -> list[str]:
    return sorted(p for p, x in net.arcs if x == t and p in net.places)


def _post(net: Net, t: str) -> list[str]:
    return sorted(p for x, p in net.arcs if x == t and p in net.places)


def _silent_search(net: Net, marking: Counter[str], pre: list[str]) -> tuple[int, Counter[str], list[str]]:
    """Breadth-first search over silent firings for the marking where the fewest places of `pre`
    are empty (fewest firings on ties). Returns that count, the marking and the silent transitions
    fired to reach it. As in pm4py, silent firings that fill only some of the places count too."""
    def lacking(m: Counter[str]) -> int:
        return sum(1 for p in pre if m[p] == 0)

    best = (lacking(marking), marking, [])
    seen = {frozenset(marking.items())}
    queue = deque([(marking, [])])
    while queue and best[0] and len(seen) <= MAX_SILENT_STATES:
        m, path = queue.popleft()
        for t in enabled(net, m):
            if net.transitions[t] is not None:
                continue
            nxt = fire(net, m, t)
            key = frozenset(nxt.items())
            if key not in seen:
                seen.add(key)
                queue.append((nxt, path + [t]))
                if lacking(nxt) < best[0]:
                    best = (lacking(nxt), nxt, path + [t])
    return best


def _closest_to(net: Net, marking: Counter[str], final: Counter[str]) -> tuple[Counter[str], list[str]]:
    """Silent-reachable marking with the fewest missing plus remaining tokens (fewest firings on ties),
    and the silent transitions fired to reach it."""
    best, best_path, best_left = marking, [], _leftover(marking, final)
    seen = {frozenset(marking.items())}
    queue = deque([(marking, [])])
    while queue and best_left and len(seen) <= MAX_SILENT_STATES:
        m, path = queue.popleft()
        for t in enabled(net, m):
            if net.transitions[t] is not None:
                continue
            nxt = fire(net, m, t)
            key = frozenset(nxt.items())
            if key not in seen:
                seen.add(key)
                queue.append((nxt, path + [t]))
                if _leftover(nxt, final) < best_left:
                    best, best_path, best_left = nxt, path + [t], _leftover(nxt, final)
    return best, best_path


def _leftover(marking: Counter[str], final: Counter[str]) -> int:
    return sum(max(marking[p] - final[p], 0) for p in marking) + sum(max(final[p] - marking[p], 0) for p in final)


def token_replay(net: Net, trace: Trace, *, complete: bool = True) -> Replay:
    """Replay the complete entries of a trace. With complete=False (a running
    case) the final consumption is not done, so remaining tokens are not
    counted and the unfinished trace is not a deviation."""
    by_label: dict[str, list[str]] = {}
    for t, label in sorted(net.transitions.items()):
        if label is not None:
            by_label.setdefault(label, []).append(t)

    marking = Counter(net.initial)
    produced, consumed = sum(net.initial.values()), 0
    missing: Counter[str] = Counter()
    problems: list[tuple[str, tuple[str, ...]]] = []

    for entry in trace.entries:
        if entry.lifecycle != "complete" or entry.activity not in by_label:
            continue
        # Several transitions can share a label: take the cheapest in missing tokens.
        best = None
        for t in by_label[entry.activity]:
            lack, reached, silent = _silent_search(net, marking, _pre(net, t))
            cand = (lack, len(silent), t, reached, silent)
            if best is None or cand[:3] < best[:3]:
                best = cand
        _, _, t, marking, silent = best
        marking = Counter(marking)
        # The silent transitions fired to enable t consume and produce tokens too (as in pm4py).
        consumed += sum(len(_pre(net, s)) for s in silent)
        produced += sum(len(_post(net, s)) for s in silent)
        lacking = [p for p in _pre(net, t) if marking[p] == 0]
        for p in lacking:
            missing[p] += 1
            marking[p] += 1
        if lacking:
            problems.append((entry.activity, entry.source_ids))
        for p in _pre(net, t):
            marking[p] -= 1
        consumed += len(_pre(net, t))
        for p in _post(net, t):
            marking[p] += 1
        produced += len(_post(net, t))
        marking = +marking

    remaining: Counter[str] = Counter()
    if complete:
        final = Counter(net.final)
        marking, silent = _closest_to(net, marking, final)
        consumed += sum(len(_pre(net, s)) for s in silent)
        produced += sum(len(_post(net, s)) for s in silent)
        for p, n in final.items():
            if marking[p] < n:
                missing[p] += n - marking[p]
        consumed += sum(final.values())
        remaining = +Counter({p: marking[p] - final[p] for p in marking if marking[p] > final[p]})

    m_total, r_total = sum(missing.values()), sum(remaining.values())
    fitness = 0.5 * (1 - m_total / consumed if consumed else 1.0) + 0.5 * (1 - r_total / produced if produced else 1.0)
    return Replay(fitness, produced, consumed, +missing, remaining, problems)
