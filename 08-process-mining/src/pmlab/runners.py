"""The run loop of each exercise. An exercise file passes its own piece in.

Every runner reads the committed logs of the unit and nothing else, and says
which log in its first line. `--log` takes a committed log name (`train`,
`holdout`, `ref-order`, ...) or the path of a .jsonl file in the same shape.
"""

import argparse
import json
import statistics
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.markup import escape

from . import ui
from .events import Event, read_events
from .log import Entry, Trace
from .recipes import Recipe, load_recipes

LOGS = ("train", "holdout", "ref-order", "ref-stuck", "ref-skip-check", "ref-no-end", "ref-prefix")
REFS = ("ref-order", "ref-stuck", "ref-skip-check", "ref-no-end", "ref-prefix")


def parser(file: str, about: str, log: str = "train") -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=f"{Path(file).name}: {about}")
    p.add_argument("--log", default=log, help="A committed log name, or the path of a .jsonl file.")
    return p


def todo(name: str) -> None:
    ui.show_todo(f"{name}()", "Write it in the exercise file first.")
    raise SystemExit(1)


# ---------------------------------------------------------------- reading the committed logs

@dataclass
class Source:
    name: str
    label: str
    raw: int                       # low-level events in the file
    events: list[Event]            # after the unit 08 rules (derive_extra)
    orders: dict[str, str]         # event id -> found order id
    recipes: dict[str, Recipe]
    truth: dict[str, Any] | None   # the true orders of a simulated log, if the file is there

    @property
    def entries(self) -> list[Entry]:
        """The reference abstraction of the log."""
        from .abstraction import abstract
        return abstract(self.events, self.recipes, self.orders)


def _injected(header: dict) -> str:
    faults = [f"{i['kind']} {i.get('operation', '')}".strip() + (f" at t={i['time']:g} s" if "time" in i else "")
              for i in header.get("injected", [])]
    return ", ".join(sorted(set(faults))) or "none"


def load(log: str) -> Source:
    from .evidence import log_path
    from .orders import correlate
    from .rules import derive_extra
    path = log_path(log) if log in LOGS else Path(log)
    header, events = read_events(path)
    recipes = load_recipes()
    derived = derive_extra(events)
    orders = correlate(derived, recipes)
    found = len(set(orders.values()))
    if log in REFS:
        label = f"{log}: a copy of the reference order (invented); injected: {_injected(header)}"
    elif log in LOGS:
        label = f"{log}: simulated log (invented), {found} orders found; injected deviations: {len(header['injected'])}"
    else:
        label = f"{path.name}: your file, {found} orders found"
    truth_file = path.with_name(path.stem + ".truth.json")
    truth = json.loads(truth_file.read_text(encoding="utf-8"))["orders"] if truth_file.exists() else None
    return Source(log if log in LOGS else path.stem, label, len(events), derived, orders, recipes, truth)


def traces_of(entries: list[Entry]) -> list[Trace]:
    from .log import to_log
    return to_log(entries)


def true_orders(src: Source, traces: list[Trace]) -> dict[str, dict]:
    """Found order id -> its true order (recipe, deviations), by a vote of the source event ids."""
    if src.truth is None:
        return {}
    owner = {e: order for order, body in src.truth.items() for e in body["event_ids"]}
    out = {}
    for t in traces:
        votes = Counter(owner[s] for e in t.entries for s in e.source_ids if s in owner)
        if votes:
            out[t.case_id] = src.truth[votes.most_common(1)[0][0]]
    return out


def _t(x: float) -> str:
    return "-" if x != x else f"{x:.1f}".rstrip("0").rstrip(".")


def _ids(ids: tuple[str, ...], most: int = 3) -> str:
    return ", ".join(ids[:most]) + (f", … ({len(ids)})" if len(ids) > most else "")


def _seq(activities: tuple[str, ...]) -> str:
    return " > ".join(activities) or "-"


def _nets(recipes: dict[str, Recipe]) -> dict:
    from .compile import compile_recipe
    return {name: compile_recipe(r) for name, r in recipes.items()}


def show_entries(title: str, entries: list[Entry]) -> None:
    ui.show_table(title, ["t (s)", "", "activity", "objects", "event ids"],
                  [(_t(e.time), e.lifecycle, e.activity, " ".join(o for o in e.objects if not o.startswith("order:")),
                    _ids(e.source_ids, 2)) for e in entries])


# ---------------------------------------------------------------- EXE00: the question end to end

def run_demo(file: str) -> None:
    p = argparse.ArgumentParser(description=f"{Path(file).name}: the 'recipe stopped' question, end to end.")
    p.add_argument("--log", default="ref-stuck", choices=LOGS, help="A committed log.")
    p.add_argument("--order", default=None, help="The order (default: the only order of the log).")
    p.add_argument("--at", type=float, default=None, help="The time of the question, s (default: the last event).")
    p.add_argument("--question", default="The recipe stopped, I don't know why.")
    p.add_argument("--no-model", action="store_true", help="Stop before the generator.")
    p.add_argument("--model", default=None, help="Generator (default qwen3:1.7b).")
    args = p.parse_args()
    from .evidence import mine, pipeline
    src = load(args.log)
    ui.show_note(f"Source: {src.label}")
    m = pipeline(args.log)
    order = args.order or sorted(m.traces)[0]
    now = args.at if args.at is not None else max(e.time for e in m.events)
    ui.show_table("From low-level events to a process", ["stage", "count"], [
        ("low-level events in the log", src.raw),
        ("events after the unit 08 rules", len(m.events)),
        ("events placed in an order (correlation)", len(m.orders)),
        ("orders found", len(m.traces)),
        ("log entries (operation start, complete)", len(m.entries)),
        ("recipes (Petri nets)", ", ".join(sorted(m.nets)))])
    trace = m.traces.get(order)
    if trace is not None:
        show_entries(f"The log of {order} up to t={_t(now)} s", [e for e in trace.entries if e.time <= now])
    f = mine(m, order, now)
    text = "\n".join(f"{i}. {line}" for i, line in enumerate(f.lines, 1))
    ui.console.print(ui.Panel(ui.Text(text), title=f"Evidence lines · {order} at t={_t(now)} s",
                              border_style="magenta"))
    if args.no_model:
        return
    from .answer import answer
    from .client import OllamaError
    try:
        a = answer(args.question, f.lines, **({"model": args.model} if args.model else {}))
    except OllamaError as error:
        ui.show_error(f"{error}\nRun with --no-model to stop at the evidence lines.")
        raise SystemExit(1) from error
    status = "refused" if a.refused else ("cites unknown ids: " + ", ".join(a.unknown) if a.unknown else "citations ok")
    ui.console.print(ui.Panel(ui.Text(a.text), title=f"Answer · {args.question}",
                              subtitle=f"{a.seconds:.1f}s · {status}", border_style="green"))


# ---------------------------------------------------------------- EXE01: the event log and the case notion

def run_to_log(to_log_fn: Callable, file: str) -> None:
    p = parser(file, "the event log: one case notion, then another.")
    p.add_argument("--order", default=None, help="The order to split by pallet (default: one with three pallets).")
    args = p.parse_args()
    from .log import to_log
    src = load(args.log)
    ui.show_note(f"Source: {src.label}")
    entries = src.entries
    try:
        mine = {n: to_log_fn(entries, n) for n in ("order", "pallet")}
    except NotImplementedError:
        todo("to_log")
    ref = {n: to_log(entries, n) for n in ("order", "pallet")}

    def measures(traces: list[Trace]) -> tuple[int, int]:
        return len(traces), sum(len(t.entries) for t in traces)

    pallets = [sum(o.startswith("pallet:") for o in e.objects) for e in entries]
    rows = [("traces", *[measures(mine[n])[0] for n in mine], *[measures(ref[n])[0] for n in ref]),
            ("entries in the traces", *[measures(mine[n])[1] for n in mine], *[measures(ref[n])[1] for n in ref])]
    ui.show_table(f"{len(entries)} entries, two case notions", ["", "order (yours)", "pallet (yours)",
                                                              "order (ref)", "pallet (ref)"], rows)
    ui.show_note(f"entries with no pallet (lost by the pallet notion): {pallets.count(0)}; "
                 f"entries with two or more pallets (copied): {sum(n >= 2 for n in pallets)}")
    same = all([(t.case_id, [e.source_ids for e in t.entries]) for t in mine[n]] ==
               [(t.case_id, [e.source_ids for e in t.entries]) for t in ref[n]] for n in mine)
    ui.show_note(f"same traces as the reference: {same}")
    by_order = {t.case_id: t for t in mine["order"]}
    order = args.order or next((t.case_id for t in mine["order"] if len(
        {o for e in t.entries for o in e.objects if o.startswith("pallet:")}) >= 3), None)
    if order not in by_order:
        return
    own = sorted({o for e in by_order[order].entries for o in e.objects if o.startswith("pallet:")},
                 key=lambda c: (len(c), c))
    rows = [(order, _seq(by_order[order].activities))]
    rows += [(p, _seq(tuple(e.activity for e in t.entries if e.case_id == order and e.lifecycle == "complete")))
             for t in mine["pallet"] for p in own if t.case_id == p]
    ui.show_table(f"{order} as one case, then as its pallets (complete entries of {order} only)",
                  ["case", "activities"], rows)
    for t in mine["pallet"]:
        if t.case_id in own:
            orders = {e.case_id for e in t.entries}
            if len(orders) > 1:
                ui.show_note(f"the whole {t.case_id} trace: {len(t.entries)} entries from {len(orders)} orders "
                             f"(the line reuses pallet ids)")


# ---------------------------------------------------------------- EXE02: event abstraction

def run_abstract(match_fn: Callable, file: str) -> None:
    p = parser(file, "low-level events become operations with a start and a complete.", log="ref-order")
    args = p.parse_args()
    from .abstraction import abstract
    src = load(args.log)
    ui.show_note(f"Source: {src.label}")
    try:
        mine = abstract(src.events, src.recipes, src.orders, match=match_fn)
    except NotImplementedError:
        todo("match_operations")
    ref = src.entries

    def measures(entries: list[Entry]) -> list[int]:
        cited = {i for e in entries for i in e.source_ids}
        unmapped = sum(e.activity.startswith("unmapped:") for e in entries)
        done = sum(e.lifecycle == "complete" for e in entries) - unmapped
        return [len(entries), done, unmapped, len(cited & set(src.orders))]

    names = ("entries", "operations completed", "unmapped entries", "order events cited by an entry")
    ui.show_table(f"{len(src.events)} events, {len(src.orders)} of them in an order", ["", "yours", "reference"],
                  list(zip(names, measures(mine), measures(ref))))

    def key(entries: list[Entry]) -> list[tuple]:
        return [(e.case_id, e.activity, e.lifecycle, e.time, e.source_ids) for e in entries]

    ui.show_note(f"same entries as the reference: {key(mine) == key(ref)}")
    first = sorted({e.case_id for e in mine}, key=lambda c: (len(c), c))[:1]
    if first:
        show_entries(f"Your entries of {first[0]}", [e for e in mine if e.case_id == first[0]])


# ---------------------------------------------------------------- EXE03: directly-follows graph

def run_dfg(dfg_fn: Callable, file: str) -> None:
    p = parser(file, "directly-follows graph, variants, rare paths.")
    p.add_argument("--min-count", type=int, default=3, help="Hide the edges seen fewer times.")
    args = p.parse_args()
    from .dfg import dfg
    from .log import variants
    src = load(args.log)
    ui.show_note(f"Source: {src.label}")
    traces = traces_of(src.entries)
    try:
        mine = dfg_fn(traces)
    except NotImplementedError:
        todo("dfg")
    ref = dfg(traces)
    keep = sorted(((e, c) for e, c in mine.edges.items() if c >= args.min_count), key=lambda x: (-x[1], x[0]))
    ui.show_table(f"Directly-follows edges seen {args.min_count} times or more",
                  ["from", "to", "count", "median gap s"],
                  [(a, b, c, _t(statistics.median(mine.times.get((a, b)) or [0.0]))) for (a, b), c in keep])
    rare = {e: c for e, c in mine.edges.items() if c < args.min_count}
    ui.show_note(f"{len(mine.edges)} edges, {len(rare)} rare ones hidden ({sum(rare.values())} pairs). "
                 f"starts {dict(mine.starts)}; ends {dict(mine.ends.most_common(4))}")
    v = variants(traces)
    ui.show_table(f"{len(v)} variants over {len(traces)} traces: the five most frequent", ["count", "activities"],
                  [(n, _seq(seq)) for seq, n in v.most_common(5)])
    same = (dict(mine.edges), dict(mine.starts), dict(mine.ends)) == (dict(ref.edges), dict(ref.starts), dict(ref.ends))
    ui.show_note(f"same edges, starts and ends as the reference: {same}")


# ---------------------------------------------------------------- EXE04: the Alpha miner

def run_alpha(alpha_fn: Callable, file: str) -> None:
    p = parser(file, "the Alpha miner, and where it fails; the pm4py inductive miner for comparison.")
    p.add_argument("--min-count", type=int, default=3, help="Frequent variants: seen this many times or more.")
    args = p.parse_args()
    from .log import variants
    from .reference import pm4py, to_pm4py, to_pm4py_log
    src = load(args.log)
    ui.show_note(f"Source: {src.label}")
    traces = [t for t in traces_of(src.entries) if t.activities]
    v = variants(traces)
    names = {r: {op.name for op in rec.operations} for r, rec in src.recipes.items()}
    groups = {
        "brick_demo": [t for t in traces if set(t.activities) <= names["brick_demo"]],
        "parts_test": [t for t in traces if "mill_part" in t.activities],
        "gadget, no fail": [t for t in traces if "assemble_gadget" in t.activities
                            and "bin_covers" not in t.activities],
        "gadget, fail": [t for t in traces if "bin_covers" in t.activities],
        "all orders": traces,
    }

    def fitness(pn, im, fm, log) -> tuple[float, int]:
        res = pm4py.conformance_diagnostics_token_based_replay(log, pn, im, fm)
        return statistics.mean(r["trace_fitness"] for r in res), sum(r["trace_is_fit"] for r in res)

    rows, nets = [], {}
    for name, every in groups.items():
        for which, ts in (("all", every), (f">= {args.min_count}", [t for t in every
                                                                     if v[t.activities] >= args.min_count])):
            if not ts:
                continue
            try:
                net = alpha_fn(ts)
            except NotImplementedError:
                todo("alpha")
            nets[(name, which)] = net
            log = to_pm4py_log(ts)
            a_fit, a_ok = fitness(*to_pm4py(net), log)
            i_fit, i_ok = fitness(*pm4py.discover_petri_net_inductive(log), log)
            rows.append((name, which, len(ts), len(net.places), f"{a_fit:.3f}", f"{a_ok}", f"{i_fit:.3f}",
                         f"{i_ok}"))
    ui.show_table("Your Alpha net and the inductive miner (pm4py): token replay on the traces they come from",
                  ["orders", "variants", "n", "alpha places", "alpha fitness", "fit", "IM fitness", "fit"], rows)
    key = ("brick_demo", "all")
    if key in nets:
        net = nets[key]
        ui.show_table("Your Alpha net of brick_demo, all traces: places", ["place", "from", "to"],
                      [(p, ", ".join(sorted(net.transitions[t] or t for t, q in net.arcs if q == p)),
                        ", ".join(sorted(net.transitions[t] or t for q, t in net.arcs if q == p)))
                       for p in sorted(net.places)])
    if groups["gadget, fail"]:
        tree = pm4py.discover_process_tree_inductive(to_pm4py_log(groups["gadget, fail"]))
        ui.console.print(ui.Panel(ui.Text(str(tree)), title="Inductive miner (pm4py): gadget, fail, all traces, "
                                                            "as a process tree", border_style="cyan"))
        ui.show_note("->( ) sequence · X( ) choice · +( ) parallel · *( do, redo ) loop · tau silent")


# ---------------------------------------------------------------- EXE05: the recipe as a Petri net

def run_compile(compile_fn: Callable, file: str) -> None:
    p = parser(file, "the recipe as a Petri net (normative model), and its play-out.")
    p.add_argument("--recipe", default="gadget", help="The recipe to show.")
    args = p.parse_args()
    from .compile import compile_recipe, play_out
    from .log import variants
    src = load(args.log)
    ui.show_note(f"Source: {src.label}")
    try:
        mine = {n: compile_fn(r) for n, r in src.recipes.items()}
    except NotImplementedError:
        todo("compile_recipe")
    net = mine[args.recipe]

    def pre(t: str) -> str:
        return ", ".join(sorted(p for p, x in net.arcs if x == t and p in net.places))

    def post(t: str) -> str:
        return ", ".join(sorted(p for x, p in net.arcs if x == t and p in net.places))

    ui.show_table(f"Your net of {args.recipe}: {len(net.places)} places, {len(net.transitions)} transitions, "
                  f"{len(net.arcs)} arcs", ["transition", "takes from", "puts into"],
                  [(t if label else f"{t} (silent)", pre(t), post(t)) for t, label in sorted(net.transitions.items())])
    languages = {n: play_out(x) for n, x in mine.items()}
    ref = {n: play_out(compile_recipe(r)) for n, r in src.recipes.items()}
    shortest = min(languages[args.recipe], key=lambda s: (len(s), s), default=())
    ui.show_note(f"play-out of {args.recipe}, up to 15 operations: {len(languages[args.recipe])} sequences; "
                 f"the shortest: {_seq(shortest)}")
    v = variants(traces_of(src.entries))
    rows = []
    for name in sorted(languages):
        inside = [n for seq, n in v.items() if seq in languages[name]]
        rows.append((name, len(languages[name]), len(inside), sum(inside)))
    none = [n for seq, n in v.items() if not any(seq in lang for lang in languages.values())]
    rows.append(("no recipe", "-", len(none), sum(none)))
    ui.show_table(f"The log against your nets: {len(v)} variants", ["recipe", "sequences in the net",
                                                                   "variants in it", "traces"], rows)
    ui.show_note(f"same languages as the reference: {languages == ref}")


# ---------------------------------------------------------------- EXE06: token replay

def _replay_rows(fn: Callable, nets: dict) -> list[tuple]:
    rows = []
    for name, complete in (("ref-order", False), ("ref-order", True), ("ref-skip-check", False),
                           ("ref-no-end", False), ("ref-stuck", True)):
        src = load(name)
        (trace,) = traces_of(src.entries)
        r = fn(nets["gadget"], trace, complete=complete)
        rows.append((name, "complete" if complete else "running", f"{r.fitness:.3f}", sum(r.missing.values()),
                     sum(r.remaining.values()), ", ".join(a for a, _ in r.problems) or "-"))
    return rows


def run_replay(replay_fn: Callable, file: str) -> None:
    args = parser(file, "token replay: fitness, missing and remaining tokens.").parse_args()
    from .replay import token_replay
    src = load(args.log)
    ui.show_note(f"Source: {src.label} (and the reference order copies)")
    nets = _nets(src.recipes)
    try:
        rows = _replay_rows(replay_fn, nets)
    except NotImplementedError:
        todo("token_replay")
    ui.show_table("The reference order and its copies on the gadget net", ["log", "replayed as", "fitness",
                                                                          "missing", "remaining", "problems at"], rows)
    _by_truth(src, nets, lambda net, t: replay_fn(net, t), lambda net, t: token_replay(net, t),
              lambda r: r.fitness < 1.0, "fitness < 1")


def _by_truth(src: Source, nets: dict, mine: Callable, ref: Callable, flagged: Callable, what: str) -> None:
    """Per injected deviation kind: how many orders the check flags, on the true recipe."""
    traces = traces_of(src.entries)
    truth = true_orders(src, traces)
    if not truth:
        return
    rows: dict[str, list[int]] = {}
    same = True
    for t in traces:
        if t.case_id not in truth:
            continue
        body = truth[t.case_id]
        a, b = mine(nets[body["recipe"]], t), ref(nets[body["recipe"]], t)
        same &= flagged(a) == flagged(b)
        for kind in [d["kind"] for d in body["deviations"]] or ["none"]:
            row = rows.setdefault(kind, [0, 0])
            row[0] += 1
            row[1] += flagged(a)
    ui.show_table(f"{src.name}: orders per injected deviation, on their true recipe", ["deviation", "orders", what],
                  [(k, *rows[k]) for k in sorted(rows, key=lambda k: (k != "none", k))])
    ui.show_note(f"the same orders flagged as by the reference: {same}")


# ---------------------------------------------------------------- EXE07: alignments

def run_align(align_fn: Callable, file: str) -> None:
    args = parser(file, "alignments: log moves, model moves, cost, with event ids.").parse_args()
    from .align import align
    src = load(args.log)
    ui.show_note(f"Source: {src.label} (and the reference order copies)")
    nets = _nets(src.recipes)
    rows = []
    try:
        for name, complete in (("ref-order", False), ("ref-skip-check", False), ("ref-no-end", False),
                               ("ref-stuck", True)):
            (trace,) = traces_of(load(name).entries)
            a = align_fn(nets["gadget"], trace, complete=complete)
            moves = [f"{mv.kind} {mv.activity}" + escape(f" [{_ids(mv.source_ids, 2)}]" if mv.source_ids else "")
                     for mv in a.moves if mv.kind != "sync"]
            rows.append((name, "complete" if complete else "running", a.cost, "; ".join(moves) or "-"))
    except NotImplementedError:
        todo("align")
    ui.show_table("The reference order and its copies on the gadget net", ["log", "aligned as", "cost",
                                                                          "non-sync moves"], rows)
    _by_truth(src, nets, lambda net, t: align_fn(net, t), lambda net, t: align(net, t),
              lambda a: a.cost > 0, "cost > 0")


# ---------------------------------------------------------------- EXE08: performance

def run_performance(performance_fn: Callable, file: str) -> None:
    args = parser(file, "service and waiting times, baselines, the bottleneck, 'stuck'.").parse_args()
    from .abstraction import operations_by_name
    from .monitor import status
    from .performance import performance
    src = load(args.log)
    ui.show_note(f"Source: {src.label}")
    traces = traces_of(src.entries)
    try:
        mine = performance_fn(traces)
    except NotImplementedError:
        todo("performance")
    ref = performance(traces)
    ops = operations_by_name(src.recipes)
    order = [op for op in ops if op in mine] + sorted(set(mine) - set(ops))
    ui.show_table("Service and waiting time per operation (s)", ["operation", "n", "p50", "p95", "max", "wait p50",
                                                                 "wait p95", "nominal"],
                  [(a, mine[a].count, _t(mine[a].p50), _t(mine[a].p95), _t(mine[a].max), _t(mine[a].wait_p50),
                    _t(mine[a].wait_p95), _t(ops[a].nominal_s) if a in ops else "-") for a in order])
    waits = {a: s.wait_p95 for a, s in mine.items() if s.wait_p95 == s.wait_p95}
    if waits:
        worst = max(waits, key=waits.get)
        ui.show_note(f"longest wait (p95) before an operation: {worst}, {_t(waits[worst])} s")
    def key(stats: dict) -> dict:
        return {a: tuple(round(x, 6) if x == x else None for x in (s.count, s.p50, s.p95, s.max, s.wait_p50,
                                                                     s.wait_p95)) for a, s in stats.items()}
    ui.show_note(f"same baselines as the reference: {key(mine) == key(ref)}")
    nets = _nets(src.recipes)
    rows = []
    for name, now in (("ref-order", 1118.0), ("ref-stuck", 1400.0)):
        (trace,) = traces_of(load(name).entries)
        st = status(trace, now, nets, src.recipes, mine)
        rows += [(name, _t(now), o.activity, _t(o.age), _t(o.p95), o.verdict) for o in st.open]
    ui.show_table("Open operations with your baselines", ["log", "now", "operation", "age", "p95", "verdict"], rows)


# ---------------------------------------------------------------- EXE09: online monitoring

def run_candidates(candidates_fn: Callable, file: str) -> None:
    args = parser(file, "which recipes can a running order still be.").parse_args()
    from .monitor import candidates, prefix_at
    src = load(args.log)
    ui.show_note(f"Source: {src.label} (and the reference order)")
    nets = _nets(src.recipes)
    (trace,) = traces_of(load("ref-order").entries)
    rows, same = [], True
    try:
        for now in (0.0, 230.0, 380.0, 380.5, 1118.0):
            prefix = prefix_at(trace, now)
            c = candidates_fn(prefix, nets)
            r = candidates(prefix, nets)
            same &= (c.recipes, c.deciding, c.claim_kind, c.deciding_ids) == (
                r.recipes, r.deciding, r.claim_kind, r.deciding_ids)
            last = prefix.entries[-1] if prefix.entries else None
            seen = f"{last.activity} ({last.lifecycle})" if last else "-"
            deciding = "; ".join(f"{a}: {'/'.join(rs)}" for a, rs in c.deciding.items()) or (
                escape(f"decided at [{_ids(c.deciding_ids, 2)}]") if c.deciding_ids else "-")
            rows.append((_t(now), seen, ", ".join(c.recipes) or "none", c.claim_kind, deciding))
    except NotImplementedError:
        todo("candidates")
    ui.show_table("ref-order, seen at a time t", ["t (s)", "last entry", "candidates", "claim", "deciding"], rows)
    traces = traces_of(src.entries)
    truth = true_orders(src, traces)
    count = Counter()
    for t in traces:
        c, r = candidates_fn(t, nets), candidates(t, nets)
        same &= (c.recipes, c.deciding, c.claim_kind, c.deciding_ids) == (
            r.recipes, r.deciding, r.claim_kind, r.deciding_ids)
        kind = "decided" if len(c.recipes) == 1 else "no recipe fits" if not c.recipes else "undecided"
        count[kind] += 1
        count["true recipe"] += len(c.recipes) == 1 and c.recipes[0] == truth.get(t.case_id, {}).get("recipe")
    right = f" ({count['true recipe']} on the true recipe)" if truth else ""
    ui.show_note(f"{src.name}, whole traces: {count['decided']} of {len(traces)} orders decided{right}, "
                 f"{count['no recipe fits']} fit no recipe, {count['undecided']} undecided")
    ui.show_note(f"same candidates as the reference on ref-order and on {src.name}: {same}")


# ---------------------------------------------------------------- EXE10: object-centric log

def run_ocel(ocel_fn: Callable, errors_fn: Callable, file: str) -> None:
    args = parser(file, "object-centric log; the errors of flattening it.").parse_args()
    from .ocel import flatten, flattening_errors, ocel
    src = load(args.log)
    ui.show_note(f"Source: {src.label}")
    entries = src.entries
    try:
        mine = ocel_fn(entries)
        errors = {t: errors_fn(mine, t) for t in ("order", "pallet")}
    except NotImplementedError:
        todo("ocel() or flattening_errors")
    ref = ocel(entries)
    types = Counter(mine.objects.values())
    ui.show_note(f"{len(mine.events)} events; objects: " + ", ".join(f"{n} {t}" for t, n in sorted(types.items())))
    rows = []
    for t in ("order", "pallet"):
        flat = flatten(mine, t)
        rows.append((t, len(flat), sum(len(x.entries) for x in flat), errors[t]["convergence"],
                     errors[t]["divergence"]))
    ui.show_table("Flatten to one case type", ["case type", "cases", "events in cases", "convergence",
                                               "divergence"], rows)
    same = mine.objects == ref.objects and errors == {t: flattening_errors(ref, t) for t in ("order", "pallet")}
    ui.show_note(f"same objects and errors as the reference: {same}")


# ---------------------------------------------------------------- EXE11: the benchmark

def run_benchmark(file: str) -> None:
    p = argparse.ArgumentParser(description=f"{Path(file).name}: dev or holdout questions, stage by stage.")
    p.add_argument("--set", choices=("dev", "holdout"), default="dev")
    p.add_argument("--model", default=None, help="Generator (default qwen3:1.7b).")
    p.add_argument("--echo", action="store_true", help="No model: the answer is the evidence lines (baseline).")
    args = p.parse_args()
    from .answer import echo, judge
    from .benchmark import DEV, HOLDOUT, load_questions, run, summary
    questions = load_questions(DEV if args.set == "dev" else HOLDOUT)
    generator = (lambda q, lines: judge(echo(lines), lines)) if args.echo else None
    rows = run(questions, model=args.model, generator=generator,
               progress=lambda r: ui.show_note(f"{r.id} {r.type}: {r.stage}"))
    ui.show_table(f"{args.set}: {len(rows)} questions", ["id", "type", "stage", "evidence", "gold cited", "notes"],
                  [(r.id, r.type, r.stage, f"{r.evidence_recall:.0%}", f"{r.cited_gold:.0%}", "; ".join(r.notes))
                   for r in rows])
    s = summary(rows)
    ui.show_note(f"right {s['right']}/{s['questions']} · stages {s['stages']} · evidence recall "
                 f"{s['evidence_recall']:.2f} · gold cited {s['gold_cited']:.2f} · answers citing unknown ids "
                 f"{s['answers_with_unknown_ids']}")


# ---------------------------------------------------------------- EXE12: improve the generator

def run_prompt_experiment(system: str, file: str) -> None:
    p = argparse.ArgumentParser(description=f"{Path(file).name}: your system prompt against the unit's, on dev.")
    p.add_argument("--model", default=None, help="Generator (default qwen3:1.7b).")
    p.add_argument("--runs", type=int, default=3, help="Runs per prompt: the generator samples.")
    p.add_argument("--baseline", action="store_true", help="Also run the unit's prompt (doubles the time).")
    p.add_argument("--holdout", action="store_true", help="Once, at the very end: the holdout set.")
    args = p.parse_args()
    from .answer import SYSTEM_PROMPT
    from .benchmark import DEV, HOLDOUT, load_questions, run
    if not system.strip():
        ui.show_todo("SYSTEM_PROMPT", "It is empty: write it in the exercise file first.")
        raise SystemExit(1)
    if args.holdout:
        ui.show_note("Holdout: run it once, with the prompt you chose on dev. Do not tune on these numbers.")
    questions = load_questions(HOLDOUT if args.holdout else DEV)
    prompts = [("yours", system)] + ([("unit", SYSTEM_PROMPT)] if args.baseline else [])
    passed: dict[str, Counter] = {name: Counter() for name, _ in prompts}
    totals: dict[str, list[int]] = {name: [] for name, _ in prompts}
    notes: dict[str, Counter] = {name: Counter() for name, _ in prompts}
    for name, text in prompts:
        for r in range(args.runs):
            rows = run(questions, model=args.model, system=text)
            totals[name].append(sum(x.stage == "NONE" for x in rows))
            for x in rows:
                passed[name][x.id] += x.stage == "NONE"
                for n in x.notes:
                    notes[name][n.split(":")[0].split("[")[0].strip()] += 1
            ui.show_note(f"{name} run {r + 1}: {totals[name][-1]}/{len(rows)} right")
    head = ["id", "type"] + [f"{name} (of {args.runs})" for name, _ in prompts]
    ui.show_table("Right answers per question", head,
                  [(q["id"], q["type"], *(passed[name][q["id"]] for name, _ in prompts)) for q in questions])
    for name, _ in prompts:
        ui.show_note(f"{name}: right per run {totals[name]}; most frequent failure notes: "
                     + "; ".join(f"{n} ({c})" for n, c in notes[name].most_common(4)))
