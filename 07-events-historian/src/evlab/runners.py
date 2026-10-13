"""The run loop of each exercise. An exercise file passes its own piece in.

Every runner works without the tailnet: it reads a cached recording, or the
invented fixture, and says which one in its first line.
"""

import argparse
import statistics
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from . import ui
from .cases import assign_cases
from .chain import chain, story
from .mapping import LOCAL_MAPPING, load_mapping
from .rules import clean, derive
from .source import DEFAULT_TRACE, load


def parser(file: str, about: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=f"{Path(file).name}: {about}")
    p.add_argument("--trace", default=DEFAULT_TRACE, help="Which cached recording to read (a logical alias).")
    p.add_argument("--speed", type=float, default=1.0, help="The recording speed to read (1 or 10).")
    p.add_argument("--fixture", action="store_true", help="Read the invented fixture instead.")
    return p


def todo(name: str) -> None:
    ui.show_todo(f"{name}()", "Write it in the exercise file first.")
    raise SystemExit(1)


# ---------------------------------------------------------------- EXE00

def run_demo(file: str) -> None:
    p = parser(file, "one pallet from value changes to a cited answer.")
    p.add_argument("--case", default="p7#1", help="The case to explain (pallet#cycle).")
    p.add_argument("--question", default="What happened to pallet 7 at the QC bay, and why?")
    p.add_argument("--no-model", action="store_true", help="Stop before the generator.")
    args = p.parse_args()
    src = load(args.trace, speed=args.speed, fixture=args.fixture)
    ui.show_note(f"Source: {src.label}")
    kept, report = clean(src.changes)
    events = assign_cases(derive(kept))
    ui.show_table("From signals to evidence", ["stage", "count"], [
        ("value changes recorded", len(src.changes)), ("real changes after cleaning", len(kept)),
        ("events derived", len(events)), ("cases (pallet#cycle)", len({e.case_id for e in events if e.case_id}))])
    c = chain(events, args.case)
    ui.console.print(ui.Panel(ui.Text("\n".join(story(c)) or "(no evidence)"), title=f"Evidence of case {args.case}",
                              border_style="magenta"))
    if args.no_model:
        return
    from .answer import answer
    from .causes import explanation_lines
    for line in explanation_lines(c):
        ui.console.print(ui.Text(line, style="dim"))
    a = answer(args.question, c)
    status = "refused" if a.refused else ("cites unknown ids: " + ", ".join(a.unknown) if a.unknown else "citations ok")
    ui.console.print(ui.Panel(ui.Text(a.text), title=f"Answer · {args.question}", subtitle=f"{a.seconds:.1f}s · {status}",
                              border_style="green"))


# ---------------------------------------------------------------- EXE01: what moves

def run_select(select_nodes: Callable[[list[dict[str, Any]]], list[dict[str, Any]]], file: str) -> None:
    args = parser(file, "the catalog: subscribe only to what moves.").parse_args()
    from .recordings import real_trace
    from .sim import Sim, SimError, sim_url
    try:
        sim_url()
    except SimError:
        ui.show_note("No ICE_SIM_URL: the catalog step needs the simulator. The check runs without it.")
        return
    mapping, _ = load_mapping(LOCAL_MAPPING)
    sim, rows = Sim(), []
    try:
        for machine in mapping.machines():
            all_nodes = sim.nodes(mapping.server(machine), trace=real_trace(args.trace), with_data=False)
            chosen = select_nodes(all_nodes)
            mapped = sum(1 for s in mapping.signals.values() if s.machine == machine)
            rows.append((machine, len(all_nodes), len(chosen), mapped))
    except NotImplementedError:
        todo("select_nodes")
    ui.show_table(f"Catalog of {args.trace} (logical machine names)",
                  ["machine", "nodes", "yours: with data", "mapped signals"], rows)


# ---------------------------------------------------------------- EXE02: when did it happen

def run_place(place: Callable[..., tuple[Any, Any, Any]], file: str) -> None:
    args = parser(file, "event time from the playback position, not from SourceTimestamp.").parse_args()
    polls = [(100.0, 0.0), (100.5, 0.5), (101.0, 1.0), (101.5, 6.0)]
    try:
        rows = [(w, *place(w, polls)) for w in (99.0, 100.25, 100.9, 101.2, 102.0)]
    except NotImplementedError:
        todo("place")
    ui.show_table("Your place() on four polls (wall s, position s)", ["wall", "event time", "lo", "hi"], rows)
    for speed in (1.0, 10.0):
        src = load(args.trace, speed=speed, fixture=args.fixture)
        widths = [c.event_time_hi - c.event_time_lo for c in src.changes if c.event_time_hi is not None]
        if widths:
            ui.show_note(f"{src.label}: bound width median {statistics.median(widths):.2f} s, "
                         f"max {max(widths):.2f} s over {len(widths)} changes")


# ---------------------------------------------------------------- EXE03: what is a change

def run_clean(clean_fn: Callable, file: str) -> None:
    args = parser(file, "which notifications are real changes.").parse_args()
    src = load(args.trace, speed=args.speed, fixture=args.fixture)
    ui.show_note(f"Source: {src.label}")
    try:
        mine, report = clean_fn(src.changes)
    except NotImplementedError:
        todo("clean")
    ref, ref_report = clean(src.changes)
    ui.show_table("Cleaning", ["", "yours", "reference"], [
        ("changes in", len(src.changes), len(src.changes)), ("kept", len(mine), len(ref)),
        *[(reason, report.dropped.get(reason, 0), n) for reason, n in ref_report.dropped.items()]])
    ui.show_note("same kept ids: " + str([c.change_id for c in mine] == [c.change_id for c in ref]))


# ---------------------------------------------------------------- EXE04: signals to events

def run_derive(derive_fn: Callable, file: str) -> None:
    args = parser(file, "signals to events, each with its evidence.").parse_args()
    src = load(args.trace, speed=args.speed, fixture=args.fixture)
    ui.show_note(f"Source: {src.label}")
    kept, _ = clean(src.changes)
    try:
        mine = derive_fn(kept)
    except NotImplementedError:
        todo("derive_missions")
    ref = [e for e in derive(kept) if e.rule in ("missions", "destinations")]
    a, b = Counter(e.activity for e in mine), Counter(e.activity for e in ref)
    ui.show_table("Events per activity", ["activity", "yours", "reference"],
                  [(k, a.get(k, 0), b.get(k, 0)) for k in sorted(set(a) | set(b))])
    same = [(e.activity, e.evidence) for e in mine] == [(e.activity, e.evidence) for e in ref]
    ui.show_note(f"same events and evidence as the reference: {same}")


# ---------------------------------------------------------------- EXE05: product cases

def run_assign_cases(assign_fn: Callable, file: str) -> None:
    args = parser(file, "product cycles and safe QC-to-pallet correlation.")
    args.add_argument("--case", default="p7#1", help="The case to inspect (pallet#cycle).")
    options = args.parse_args()
    src = load(options.trace, speed=options.speed, fixture=options.fixture)
    kept, _ = clean(src.changes)
    events = derive(kept)
    try:
        mine = assign_fn(events)
    except NotImplementedError:
        todo("assign_cases")
    reference = assign_cases(events)
    ui.show_note(f"Source: {src.label}")
    ui.show_table("Case assignment", ["measure", "yours", "reference"], [
        ("events", len(mine), len(reference)),
        ("case-labelled events", sum(e.case_id is not None for e in mine),
         sum(e.case_id is not None for e in reference)),
        ("inferred links", sum(e.claim_kind == "inferred" for e in mine),
         sum(e.claim_kind == "inferred" for e in reference)),
    ])
    same = [(e.event_id, e.case_id, e.pallet, e.claim_kind) for e in mine] == \
        [(e.event_id, e.case_id, e.pallet, e.claim_kind) for e in reference]
    ui.show_note(f"same case labels and claim kinds as the reference: {same}")
    ui.console.print(ui.Panel(ui.Text("\n".join(story(chain(mine, options.case))) or "(no evidence)"),
                              title=f"Case {options.case}", border_style="magenta"))


# ---------------------------------------------------------------- EXE06: evidence chain

def run_chain(chain_fn: Callable, file: str) -> None:
    args = parser(file, "the evidence chain: visits, events, and coverage.")
    args.add_argument("--case", default="p7#1", help="The case to inspect (pallet#cycle).")
    options = args.parse_args()
    src = load(options.trace, speed=options.speed, fixture=options.fixture)
    kept, _ = clean(src.changes)
    events = assign_cases(derive(kept))
    try:
        mine = chain_fn(events, options.case)
    except NotImplementedError:
        todo("chain")
    reference = chain(events, options.case)
    ui.show_note(f"Source: {src.label}")
    ui.show_table("Evidence chain", ["measure", "yours", "reference"], [
        ("steps", len(mine.steps), len(reference.steps)),
        ("visits", len(mine.visits), len(reference.visits)),
        ("loop evidence", mine.loop_events, reference.loop_events),
        ("coverage notes", len(mine.coverage), len(reference.coverage)),
    ])
    ui.console.print(ui.Panel(ui.Text("\n".join(story(mine)) or "(no evidence)"),
                              title=f"Case {options.case}", border_style="magenta"))


# ---------------------------------------------------------------- EXE07: the cited answer

def run_answer(messages_fn: Callable, file: str) -> None:
    p = parser(file, "the generator reads evidence lines and cites them.")
    p.add_argument("--case", default="p7#1")
    p.add_argument("--question", default="Why did robot_b drop covers in the bin?")
    args = p.parse_args()
    from .answer import Answer, REFUSAL, cited_ids
    from .client import DEFAULT_CHAT_MODEL, chat
    src = load(args.trace, speed=args.speed, fixture=args.fixture)
    ui.show_note(f"Source: {src.label}")
    kept, _ = clean(src.changes)
    c = chain(assign_cases(derive(kept)), args.case)
    try:
        msgs = messages_fn(args.question, c)
    except NotImplementedError:
        todo("messages")
    if not msgs[0]["content"].strip():
        ui.show_todo("SYSTEM_PROMPT", "It is empty: write it in the exercise file first.")
        raise SystemExit(1)
    ui.console.print(ui.Panel(ui.Text(msgs[1]["content"]), title="What the generator reads", border_style="magenta"))
    result = chat(DEFAULT_CHAT_MODEL, msgs, max_tokens=400)
    cited = cited_ids(result.content)
    unknown = [i for i in cited if i not in set(c.ids)]
    status = "refused" if REFUSAL.lower().rstrip(".") in result.content.lower() else (
        f"cites unknown ids {unknown}" if unknown else f"cites {len(cited)} known ids")
    ui.console.print(ui.Panel(ui.Text(result.content), title="Answer", subtitle=f"{result.seconds:.1f}s · {status}",
                              border_style="green"))


# ---------------------------------------------------------------- EXE08: the benchmark

def run_benchmark(file: str) -> None:
    p = argparse.ArgumentParser(description=f"{Path(file).name}: dev or holdout questions, stage by stage.")
    p.add_argument("--set", choices=("dev", "holdout"), default="dev")
    p.add_argument("--model", default=None, help="Generator (default qwen3:1.7b).")
    args = p.parse_args()
    from .benchmark import DEV, HOLDOUT, load_questions, run, summary
    questions = load_questions(DEV if args.set == "dev" else HOLDOUT)
    rows = run(questions, model=args.model, progress=lambda r: ui.show_note(f"{r.id} {r.type}: {r.stage}"))
    ui.show_table(f"{args.set}: {len(rows)} questions", ["id", "type", "stage", "evidence", "gold cited", "notes"],
                  [(r.id, r.type, r.stage, f"{r.evidence_recall:.0%}", f"{r.cited_gold:.0%}", "; ".join(r.notes))
                   for r in rows])
    s = summary(rows)
    ui.show_note(f"right {s['right']}/{s['questions']} · stages {s['stages']} · evidence recall "
                 f"{s['evidence_recall']:.2f} · gold cited {s['gold_cited']:.2f} · answers citing unknown ids "
                 f"{s['answers_with_unknown_ids']}")
