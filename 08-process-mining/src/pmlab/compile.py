"""Compile a recipe into a workflow net, and play the net out into its language.

Encoding:
- One labelled transition per operation; its id and its label are the name.
- One place per dependency edge between main operations: `A>B`. An operation
  with several successors is an AND split, with several dependencies an AND join.
- Main operations without dependencies take their token from `source`; main
  operations without main successors put their token into `sink`. When there
  are several, a silent `start` (or `end`) transition splits (or joins).
- A main operation M with fail operations after it is an XOR: M puts its token
  in `M?`. A silent `M:pass` moves it on to the main successors; the first fail
  operation takes it instead, the fail chain runs, and the last fail operation
  puts back the tokens of every input place of M, so M runs again.
"""

from collections import Counter

from pmlab.petri import Net, enabled, fire
from pmlab.recipes import Recipe

SOURCE, SINK = "source", "sink"


def _arc(net: Net, a: str, b: str) -> None:
    net.arcs.add((a, b))
    for x in (a, b):
        if x not in net.transitions:
            net.places.add(x)


def compile_recipe(recipe: Recipe) -> Net:
    """Workflow net of a recipe: one source place, one sink place."""
    ops = {op.name: op for op in recipe.operations}
    main = [op.name for op in recipe.operations if op.branch == "main"]
    fail = [op.name for op in recipe.operations if op.branch == "fail"]
    succ = {m: [x for x in main if m in ops[x].depends] for m in main}
    fail_succ = {f: [x for x in fail if f in ops[x].depends] for f in ops}

    net = Net(set(), {name: name for name in ops}, set(), Counter({SOURCE: 1}), Counter({SINK: 1}))
    net.places |= {SOURCE, SINK}

    for m in main:
        if fail_succ[m] and not (ops[m].depends and succ[m]):
            raise ValueError(f"fail branch after {m}: {m} needs a dependency and a main successor")

    roots = [m for m in main if not ops[m].depends]
    leaves = [m for m in main if not succ[m]]
    if len(roots) == 1:
        _arc(net, SOURCE, roots[0])
    else:
        net.transitions["start"] = None
        _arc(net, SOURCE, "start")
        for r in roots:
            _arc(net, "start", f"start>{r}")
            _arc(net, f"start>{r}", r)
    if len(leaves) == 1:
        _arc(net, leaves[0], SINK)
    else:
        net.transitions["end"] = None
        _arc(net, "end", SINK)
        for leaf in leaves:
            _arc(net, leaf, f"{leaf}>end")
            _arc(net, f"{leaf}>end", "end")

    for m in main:
        outs = [f"{m}>{x}" for x in succ[m]]
        for x, place in zip(succ[m], outs):
            _arc(net, place, x)
        if not fail_succ[m]:
            for place in outs:
                _arc(net, m, place)
            continue
        # XOR: pass (silent) to the main successors, or fail into the fail chain.
        decide, ok = f"{m}?", f"{m}:pass"
        net.transitions[ok] = None
        _arc(net, m, decide)
        _arc(net, decide, ok)
        for place in outs:
            _arc(net, ok, place)
        for f in fail_succ[m]:
            _arc(net, decide, f)

    for f in fail:
        nexts = fail_succ[f]
        for x in nexts:
            _arc(net, f, f"{f}>{x}")
            _arc(net, f"{f}>{x}", x)
        if not nexts:
            target = _loop_target(ops, f)
            for place in sorted(p for p, t in net.arcs if t == target and p in net.places):
                _arc(net, f, place)
    return net


def _loop_target(ops: dict, f: str) -> str:
    """The main operation that the fail chain ending in f starts from."""
    while ops[f].branch == "fail":
        (f,) = ops[f].depends
    return f


def play_out(net: Net, *, max_len: int = 15, limit: int = 1000) -> set[tuple[str, ...]]:
    """All visible label sequences of length <= max_len that reach the final marking.

    The bound max_len cuts loops: with the default 15 the gadget fail loop runs
    at most twice (9 main operations + 2 * 3), and the language of each recipe
    stays under the default limit. Raise ValueError when the language holds
    more than `limit` sequences (the result would be partial).

    The result is complete only for nets without silent cycles. A silent cycle
    is cut: a state already on the current path is not entered again, so some
    sequences can be missing.
    """
    memo: dict[tuple, frozenset[tuple[str, ...]]] = {}
    on_path: set[tuple] = set()
    final = +Counter(net.final)

    def suffixes(marking: Counter[str], budget: int) -> frozenset[tuple[str, ...]]:
        key = (frozenset(marking.items()), budget)
        if key in memo:
            return memo[key]
        if key in on_path:
            return frozenset()
        on_path.add(key)
        out: set[tuple[str, ...]] = {()} if marking == final else set()
        for t in enabled(net, marking):
            label = net.transitions[t]
            if label is not None and budget == 0:
                continue
            nxt = fire(net, marking, t)
            rest = suffixes(nxt, budget - (label is not None))
            out |= rest if label is None else {(label, *s) for s in rest}
            if len(out) > limit:
                raise ValueError(f"more than {limit} sequences up to length {max_len}")
        on_path.discard(key)
        memo[key] = frozenset(out)
        return memo[key]

    return set(suffixes(+Counter(net.initial), max_len))
