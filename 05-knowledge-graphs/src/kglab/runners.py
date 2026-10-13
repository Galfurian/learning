"""The run loop of each exercise. An exercise file passes its own piece in."""

import json
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

import yaml

from . import ui
from .benchmark import diagnose, missing_gold_edges, stages_text
from .builder import BuildReport
from .client import OllamaError, ollama_url
from .corpus import DEV_QUESTIONS, HOLDOUT_QUESTIONS, MODELS_DIR
from .evalset import Question, load_questions
from .exercise import parser, select_questions, tracer
from .extract import LINK_RELATIONS, Extraction
from .graph import Graph
from .metrics import answer_scores, mean, path_correct, triple_scores
from .pipelines import GraphRun, generate, run_chunks, run_graph
from .planner import DEFAULT_RULES, RulePlanner
from .retriever import ChunkRetriever
from .scenario import SCENARIO
from .world import World

ACTORS = [
    ("APP", "The exercise file and src/kglab: parser, graph, resolver, planner, context, checks."),
    ("GENERATIVE MODEL", "Extracts triples from prose (once per chunk, cached), and writes the answers."),
    ("RERANKER", "MiniLM cross-encoder, chunk RAG only: reorders the BM25 candidates."),
]


def fail(exc: Exception) -> None:
    ui.show_error(str(exc))
    raise SystemExit(1) from None


def link_triples(graph: Graph) -> set[tuple[str, str, str]]:
    return {(e.s, e.r, e.o) for e in graph.edges if e.r in LINK_RELATIONS}


def progress(i: int, n: int, chunk, extraction: Extraction) -> None:
    if extraction.seconds and i in (1, n) or i % 10 == 0:
        ui.show_note(f"extraction {i}/{n} · {chunk.id} · {len(extraction.triples)} mentions")


def built_world(world: World, args) -> tuple[Graph, BuildReport, Any]:
    ui.show_note(f"built graph: links extracted by {world.extract_model} (cached per chunk; "
                 f"the first run takes minutes on a CPU)")
    extractions = world.extractions(progress=progress, tracer=tracer(args))
    return world.built(extractions)


# ---------------------------------------------------------------- EXE00: the demo

def run_demo(file: str) -> None:
    p = parser(f"{Path(file).name}: the same question through chunk RAG and through a graph.",
               generation=True, extraction=True)
    p.add_argument("--pipeline", choices=("all", "chunks", "gold", "built"), default="all")
    args = p.parse_args()
    if args.verbose:
        ui.show_actors(ACTORS)
    world = World(args.extract_model)
    questions = load_questions(DEV_QUESTIONS)
    ui.show_note(f"Ollama: {ollama_url()} · scenario {SCENARIO.name} · generator {args.model}")
    if args.inspect:
        ui.show_note(f"{len(world.tree.nodes)} tree nodes from the data models, {len(world.notes)} prose chunks, "
                     f"{len(link_triples(world.gold))} gold links, {len(questions)} dev questions. No model was called.")
        return
    try:
        selected = select_questions(args, questions)
        want = ("chunks", "gold", "built") if args.pipeline == "all" else (args.pipeline,)
        planner = RulePlanner(DEFAULT_RULES)
        retriever = ChunkRetriever("bm25", "minilm") if "chunks" in want else None
        built = built_world(world, args) if "built" in want else None
        table = []
        for number, q in enumerate(selected, start=1):
            if not args.eval:
                ui.show_question(number, len(selected), q.question)
            row = [q.id, q.type]
            for name in want:
                if name == "chunks":
                    hits = retriever.top(q.question, 3)
                    run = run_chunks(q, [h.chunk for h in hits], world.gold, model=args.model, tracer=tracer(args))
                    context, answer = run.context, run.answer
                else:
                    graph, linker = (world.gold, world.gold_linker) if name == "gold" else (built[0], built[2])
                    grun = run_graph(q, graph, linker, planner, model=args.model, tracer=tracer(args))
                    context, answer = grun.context, grun.answer
                    if not args.eval:
                        ui.show_plan(grun.plan, grun.starts)
                if not args.eval:
                    ui.show_context(context, f"Context · {name}")
                    ui.show_answer(answer, args.model)
                row.append("right" if answer.score.ok else ("refused" if answer.score.refused else "wrong"))
            table.append(row)
        if len(table) > 1 and all(q.scored for q in selected):
            ui.show_table("Answers", ["id", "type", *want], table)
            by_type = []
            for t in ("single", "multi-hop", "aggregation", "alias", "no-answer"):
                rows = [r for r in table if r[1] == t]
                if rows:
                    by_type.append([t, len(rows), *(sum(r[2 + i] == "right" for r in rows) for i in range(len(want)))])
            ui.show_table("Right answers per question type", ["type", "questions", *want], by_type)
    except (OllamaError, RuntimeError) as exc:
        fail(exc)


# ---------------------------------------------------------------- EXE01: the data model as a tree

def run_parse(parse_model: Callable[..., Graph], file: str) -> None:
    p = parser(f"{Path(file).name}: data model YAML -> tree triples, no model.")
    p.add_argument("--device", help="Show the tree of this device (a file name without .yml).")
    args = p.parse_args()
    files = sorted(MODELS_DIR.glob("*.yml"))
    if args.inspect:
        ui.show_note(f"{len(files)} data model files in {MODELS_DIR}")
        return
    try:
        mine = Graph()
        for path in files:
            parse_model(yaml.safe_load(path.read_text(encoding="utf-8")), f"models/{path.name}", mine)
    except NotImplementedError:
        ui.show_todo("parse_model()", "Write it in the exercise file first.")
        raise SystemExit(1) from None
    world = World()
    ref = world.tree
    if args.device:
        rows = [(e.s, e.r, e.o, e.source) for e in mine.edges if e.s.split("/")[0] == args.device
                or e.o.split("/")[0] == args.device]
        ui.show_table(f"Your tree · {args.device}", ["subject", "relation", "object", "source"], rows)
    counts = Counter(e.r for e in mine.edges)
    ref_counts = Counter(e.r for e in ref.edges)
    ui.show_table("Edges per relation", ["relation", "yours", "reference"],
                  [(r, counts.get(r, 0), ref_counts[r]) for r in sorted(set(counts) | set(ref_counts))])
    s = triple_scores(mine.triples(), ref.triples())["all"]
    ui.show_note(f"{len(mine.nodes)} nodes (reference {len(ref.nodes)}), {len(mine.edges)} edges "
                 f"(reference {len(ref.edges)}) · same edges: precision {s.precision:.2f}, recall {s.recall:.2f}")
    links = len(link_triples(world.gold))
    ui.show_note(f"Links between devices in the tree: {len(link_triples(mine))}. In the gold graph: {links}. "
                 f"The data models give the tree; the links are in the prose.")


# ---------------------------------------------------------------- EXE02: traversal

def run_follow(follow: Callable[..., list[str]], file: str) -> None:
    args = parser(f"{Path(file).name}: follow relation paths, on the tree only and on the gold graph.").parse_args()
    world = World()
    questions = [q for q in select_questions(args, load_questions(DEV_QUESTIONS)) if q.gold_path]
    if args.inspect:
        ui.show_note(f"{len(questions)} dev questions with a gold path. No model is used in this exercise.")
        return
    rows, right = [], Counter()
    try:
        for q in questions:
            tree = follow(world.tree, q.gold_path.start, q.gold_path.relations)
            gold = follow(world.gold, q.gold_path.start, q.gold_path.relations)
            ok_tree = set(tree) == set(q.gold_answers)
            ok_gold = set(gold) == set(q.gold_answers)
            right["tree"] += ok_tree
            right["gold"] += ok_gold
            rows.append((q.id, q.type, " -> ".join(q.gold_path.relations), "✓" if ok_tree else len(tree),
                         "✓" if ok_gold else len(gold)))
    except NotImplementedError:
        ui.show_todo("follow()", "Write it in the exercise file first.")
        raise SystemExit(1) from None
    ui.show_table("Gold paths on two graphs (✓ = the gold answers, else how many nodes came back)",
                  ["id", "type", "path", "tree only", "gold graph"], rows)
    ui.show_note(f"right answer sets: tree only {right['tree']}/{len(questions)}, gold graph "
                 f"{right['gold']}/{len(questions)}")


# ---------------------------------------------------------------- EXE03: extraction

def run_extract(parse_triples: Callable[[str], Any], file: str) -> None:
    p = parser(f"{Path(file).name}: prose chunk -> JSON triples -> your parser.", extraction=True)
    p.add_argument("--chunk", type=int, help="Show chunk N (1-based) of the notes.")
    p.add_argument("--free", action="store_true", help="No enum on the relation: count the invalid ones.")
    args = p.parse_args()
    world = World(args.extract_model)
    if args.inspect:
        ui.show_chunks(world.notes, limit=12)
        return
    from .extract import extract
    from .scorecache import ScoreCache

    def run(chunk) -> Extraction:
        e = extract(chunk.title, chunk.text, model=args.extract_model, constrained=not args.free,
                    cache=ScoreCache(), tracer=tracer(args))
        valid, invalid = parse_triples(e.raw)       # your parser, on the raw JSON text
        return Extraction(valid, invalid, e.seconds, e.raw)

    try:
        chunks = world.notes if args.chunk is None else [world.notes[args.chunk - 1]]
        extractions = {}
        for i, c in enumerate(chunks, start=1):
            extractions[c.id] = run(c)
            if args.chunk is not None:
                ui.console.print(ui.Panel(c.text, title=f"Chunk {c.id}", border_style="white"))
                ui.show_raw(extractions[c.id].raw, title=f"Raw output · {args.extract_model} · "
                                                        f"{extractions[c.id].seconds:.1f}s (first run)")
            else:
                progress(i, len(chunks), c, extractions[c.id])
    except NotImplementedError:
        ui.show_todo("parse_triples()", "Write it in the exercise file first.")
        raise SystemExit(1) from None
    except (OllamaError, RuntimeError) as exc:
        fail(exc)
    from .builder import build
    graph, report = build(world.tree, world.glossary, chunks, extractions, ambiguous=world.ambiguous)
    ids = {c.id for c in chunks}
    gold = {(e.s, e.r, e.o) for e in world.gold.edges if e.r in LINK_RELATIONS and e.source in ids}
    if args.chunk is not None:
        mentions = [(m.subject, m.relation, m.object) for e in extractions.values() for m in e.triples]
        ui.show_table("Your valid mentions", ["subject", "relation", "object"], mentions)
        kept = sorted(link_triples(graph))
        ui.show_table("Resolved to nodes (kept in the graph; ✓ = gold)", ["subject", "relation", "object", "gold"],
                      [(*t, "✓" if t in gold else "") for t in kept])
        ui.show_table("Gold links of this chunk", ["subject", "relation", "object"], sorted(gold))
    scores = triple_scores(link_triples(graph), gold)
    ui.show_table("Links against gold", ["relation", "precision", "recall", "F1", "right/predicted/gold"],
                  [(r, s.precision, s.recall, s.f1, f"{s.tp}/{s.predicted}/{s.gold}") for r, s in scores.items()])
    seconds = [e.seconds for e in extractions.values()]
    ui.show_note(f"{report.mentions} valid mentions, {report.invalid} invalid, {report.kept} links kept; "
                 f"ends not resolved: {dict(report.unresolved)} · {mean(seconds):.1f}s per chunk on the first run")


# ---------------------------------------------------------------- EXE04: resolution

def run_resolve(normalize: Callable[[str], str], resolve: Callable[..., tuple[str | None, str]], file: str) -> None:
    from collections import defaultdict

    from .metrics import AMBIGUOUS, resolution_counts

    args = parser(f"{Path(file).name}: mentions in the prose -> nodes, exact then normalized.").parse_args()
    world = World()
    mentions = json.loads(SCENARIO.path("mentions").read_text(encoding="utf-8"))
    if args.inspect:
        ui.show_note(f"{len(mentions)} mentions with their gold node, from {SCENARIO.path('mentions').name}")
        return
    exact, normal = defaultdict(set), defaultdict(set)
    try:
        for node in world.gold.nodes.values():
            exact[node.id].add(node.id)
            if node.name:
                exact[node.name].add(node.id)
            for name in [node.id, node.name, *node.aliases]:
                if name:
                    normal[normalize(name)].add(node.id)
        for mention, nodes in world.ambiguous.items():
            normal[normalize(mention)].update(nodes)
        results = [(m, *resolve(m["mention"], exact, normal)) for m in mentions]
    except NotImplementedError:
        ui.show_todo("normalize() and resolve()", "Write them in the exercise file first.")
        raise SystemExit(1) from None
    pairs_exact = [(next(iter(exact[m["mention"]])) if len(exact.get(m["mention"], ())) == 1 else None, m["node"])
                   for m in mentions]
    pairs = [(node, m["node"]) for m, node, _ in results]
    # The library's Linker also knows the type the relation expects and the devices the chunk names.
    from .builder import Linker
    linker, text = Linker(world.gold, ambiguous=world.ambiguous), {c.id: c.text for c in world.notes}
    pairs_scoped = []
    for m in mentions:
        types = tuple({world.gold.nodes[c].type for c in m.get("candidates", [m["node"]]) if c in world.gold.nodes})
        pairs_scoped.append((linker.resolve(m["mention"], types, text.get(m["chunk"], "")).node, m["node"]))
    rows = []
    for label, p in (("exact only", pairs_exact), ("yours", pairs), ("+ type and chunk scope", pairs_scoped)):
        c = resolution_counts(p)
        rows.append((label, c.right, c.wrong, c.unresolved, c.ambiguous_ok, c.ambiguous_missed, c.accuracy))
    ui.show_table(f"{len(mentions)} mentions", ["resolver", "right", "wrong (merge)", "none (split)",
                                                "ambiguous ok", "ambiguous missed", "accuracy"], rows)
    levels = Counter(level for _, _, level in results)
    ui.show_note(f"your levels: {dict(levels)}")
    misses = [(m["mention"], m["chunk"], m["node"], node or "-") for m, node, _ in results if node != m["node"]]
    ui.show_table("Not right (first 15)", ["mention", "chunk", "gold", "yours"], misses[:15])
    if AMBIGUOUS in {m["node"] for m in mentions}:
        ui.show_note("An ambiguous mention is right only if the resolver says it is ambiguous.")


# ---------------------------------------------------------------- EXE05-EXE07 and the benchmark: graph runs

def graph_rows(questions: list[Question], world: World, graph: Graph, linker, planner, report: BuildReport | None,
               *, generator: bool, model: str, args) -> list[dict[str, Any]]:
    rows = []
    for q in questions:
        run = run_graph(q, graph, linker, planner, generator=generator, model=model, tracer=tracer(args))
        rows.append(row(run, world.gold, graph, report))
    return rows


def row(run: GraphRun, gold: Graph, graph: Graph, report: BuildReport | None) -> dict[str, Any]:
    q = run.question
    s = answer_scores(run.nodes, q.gold_answers)
    missing = missing_gold_edges(q, gold, graph) if q.answerable else []
    return {
        "id": q.id, "type": q.type, "answerable": q.answerable,
        "plan_path": list(run.plan.path) if run.plan else None,
        "gold_path": list(q.gold_path.relations) if q.gold_path else None,
        "path_ok": path_correct(run.plan.path if run.plan else None, q.gold_path.relations if q.gold_path else None),
        "starts": run.start_ids, "gold_starts": list(q.gold_path.start) if q.gold_path else [],
        "nodes": run.nodes, "gold_answers": list(q.gold_answers),
        "precision": s.precision, "recall": s.recall,
        "answer": run.answer.text, "answer_ok": run.answer.score.ok if run.answer.score else None,
        "missing_edges": [[e.s, e.r, e.o, e.source] for e in missing],
        "dropped_relations": sorted({(cid, m.relation) for cid, m, _ in (report.dropped if report else [])
                                     if cid in {e.source for e in missing}}),
        "stage": diagnose(run, gold, graph, report),
    }


def run_plan(plan: Callable[[str], Any], file: str) -> None:
    p = parser(f"{Path(file).name}: question -> plan (start mentions, relation path); scored on the gold graph.")
    p.add_argument("--llm", action="store_true", help="Compare with the LLM planner (qwen3:1.7b, JSON schema).")
    args = p.parse_args()
    world = World()
    questions = select_questions(args, load_questions(DEV_QUESTIONS))
    if args.inspect:
        ui.show_note(f"{len(questions)} dev questions; the planner runs without a model unless --llm.")
        return

    class Yours:
        def plan(self, text: str):
            return plan(text)

    planners = [("yours", Yours())]
    if args.llm:
        from .planner import LLMPlanner
        from .scorecache import ScoreCache
        planners.append(("llm", LLMPlanner(cache=ScoreCache(), tracer=tracer(args))))
    try:
        table = []
        for name, planner in planners:
            rows = graph_rows(questions, world, world.gold, world.gold_linker, planner, None,
                              generator=False, model="", args=args)
            if len(questions) == 1:
                r = rows[0]
                ui.show_table(f"{name}", ["", "value"], [(k, r[k]) for k in ("plan_path", "gold_path", "starts",
                                                                              "gold_starts", "nodes", "gold_answers")])
            table.append((name, f"{sum(r['path_ok'] for r in rows)}/{len(rows)}",
                          f"{sum(set(r['starts']) == set(r['gold_starts']) for r in rows if r['gold_path'])}/"
                          f"{sum(1 for r in rows if r['gold_path'])}",
                          mean([r["recall"] for r in rows if r["answerable"]]),
                          stages_text([r["stage"] for r in rows])))
        ui.show_table("Planners on the gold graph", ["planner", "path right", "start right", "answer recall",
                                                      "first failing stage"], table)
    except NotImplementedError:
        ui.show_todo("plan()", "Write it in the exercise file first.")
        raise SystemExit(1) from None
    except (OllamaError, RuntimeError) as exc:
        fail(exc)


def run_facts(facts_context: Callable[..., Any], file: str) -> None:
    from . import pipelines

    p = parser(f"{Path(file).name}: graph facts as context, against chunks, per question type.",
               generation=True, extraction=True)
    args = p.parse_args()
    world = World(args.extract_model)
    questions = select_questions(args, load_questions(DEV_QUESTIONS))
    if args.inspect:
        ui.show_note(f"{len(questions)} dev questions · generator {args.model} · three pipelines")
        return
    pipelines.facts_context = facts_context          # run_graph now builds the context with your function
    try:
        run_demo_rows(questions, world, args)
    except NotImplementedError:
        ui.show_todo("facts_context()", "Write it in the exercise file first.")
        raise SystemExit(1) from None
    except (OllamaError, RuntimeError) as exc:
        fail(exc)


def run_demo_rows(questions: list[Question], world: World, args) -> None:
    planner = RulePlanner(DEFAULT_RULES)
    retriever = ChunkRetriever("bm25", "minilm")
    built, report, linker = built_world(world, args)
    table = []
    for q in questions:
        chunk_run = run_chunks(q, [h.chunk for h in retriever.top(q.question, 3)], world.gold, model=args.model)
        gold_run = run_graph(q, world.gold, world.gold_linker, planner, model=args.model)
        built_run = run_graph(q, built, linker, planner, model=args.model)
        if len(questions) == 1:
            for name, ctx, ans in (("chunks", chunk_run.context, chunk_run.answer),
                                   ("gold", gold_run.context, gold_run.answer),
                                   ("built", built_run.context, built_run.answer)):
                ui.show_context(ctx, f"Context · {name}")
                ui.show_answer(ans, args.model)
        table.append((q.id, q.type, *(("right" if a.score.ok else "wrong") for a in
                                      (chunk_run.answer, gold_run.answer, built_run.answer)),
                      *(("ok" if a.citations.ok else "bad") for a in (chunk_run.answer, gold_run.answer, built_run.answer))))
    if len(table) > 1:
        by_type = []
        for t in ("single", "multi-hop", "aggregation", "alias", "no-answer"):
            rows = [r for r in table if r[1] == t]
            if rows:
                by_type.append([t, len(rows), *(sum(r[2 + i] == "right" for r in rows) for i in range(3))])
        ui.show_table("Right answers per question type", ["type", "questions", "chunks", "gold graph", "built graph"],
                      by_type)
        ui.show_note("citations ok: " + ", ".join(f"{n} {sum(r[5 + i] == 'ok' for r in table)}/{len(table)}"
                                                   for i, n in enumerate(("chunks", "gold", "built"))))


ROWS_DIR = Path(__file__).resolve().parents[2] / ".cache" / "rows"
ROWS_VERSION = 2   # bump when row() changes its keys


def run_diagnosis(diagnose_row: Callable[[dict], str], file: str) -> None:
    p = parser(f"{Path(file).name}: the first failing stage of each dev question, built graph.",
               generation=True, extraction=True)
    args = p.parse_args()
    world = World(args.extract_model)
    # The rows depend on both models and on the row format: all three are in the file name.
    name = f"dev-built-{args.extract_model}-{args.model}-v{ROWS_VERSION}".replace(":", "_").replace("/", "_")
    path = ROWS_DIR / f"{name}.json"
    if args.inspect:
        ui.show_note(f"rows file: {path} ({'present' if path.exists() else 'missing: the first run writes it'})")
        return
    try:
        if not path.exists():
            built, report, linker = built_world(world, args)
            rows = graph_rows(load_questions(DEV_QUESTIONS), world, built, linker, RulePlanner(DEFAULT_RULES), report,
                              generator=True, model=args.model, args=args)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(rows, indent=1) + "\n", encoding="utf-8")
        rows = json.loads(path.read_text(encoding="utf-8"))
        table = [(r["id"], r["type"], diagnose_row(r), r["stage"]) for r in rows]
    except NotImplementedError:
        ui.show_todo("diagnose()", "Write it in the exercise file first.")
        raise SystemExit(1) from None
    except (OllamaError, RuntimeError) as exc:
        fail(exc)
    ui.show_table("First failing stage", ["id", "type", "yours", "reference"], table)
    same = sum(a == b for _, _, a, b in table)
    ui.show_note(f"same label as the reference: {same}/{len(table)} · yours: {stages_text([t[2] for t in table])}")


# ---------------------------------------------------------------- EXE08: the benchmark on the holdout

def run_benchmark(file: str) -> None:
    p = parser(f"{Path(file).name}: chunk RAG, gold graph, built graph on the holdout.",
               generation=True, extraction=True)
    args = p.parse_args()
    world = World(args.extract_model)
    questions = select_questions(args, load_questions(HOLDOUT_QUESTIONS))
    if args.inspect:
        ui.show_note(f"{len(questions)} holdout questions. Run them once, after every choice is made on dev.")
        return
    try:
        run_demo_rows(questions, world, args)
    except (OllamaError, RuntimeError) as exc:
        fail(exc)
