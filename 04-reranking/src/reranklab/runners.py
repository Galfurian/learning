"""The run loop of each exercise. An exercise file passes its own pieces in."""

from pathlib import Path

from . import ui
from .client import OllamaError, ollama_url, render_prompt
from .corpus import DEV_QUESTIONS
from .evalset import load_questions
from .exercise import parser, select_questions, tracer
from .metrics import ideal_gains, metric_row
from .rerankers import make_reranker, rerank
from .retriever import FirstStage, plant_chunks
from .benchmark import row, run_question

# EXE06 reads tev1 quality from the score cache written by the library Tev1Reranker.
TEV1_FILL_HINT = "run: uv run python exercises/exe00-demo/exe00.py --reranker tev1-a --eval --depth {depth}"

ACTORS = [
    ("APP", "The exercise file and src/reranklab: candidates, reranking, context, checks."),
    ("EMBEDDING MODEL", "First stage: one vector per text, the question never meets a chunk."),
    ("RERANKER", "Second stage: reads the question and one candidate together, returns a relevance score."),
    ("GENERATIVE MODEL", "Reads only the top k chunks, writes the answer."),
]


def run_demo(file: str) -> None:
    args = parser(f"{Path(file).name}: first stage -> reranker -> generator.", generation=True).parse_args()
    if args.verbose:
        ui.show_actors(ACTORS)
    ui.show_note(f"Ollama: {ollama_url()} · first stage {args.first_stage}, depth {args.depth} · "
                 f"reranker {args.reranker}, top {args.top_k}")
    chunks = plant_chunks()
    questions = load_questions(DEV_QUESTIONS)
    if args.inspect:
        ui.show_note(f"{len(chunks)} chunks, {len(questions)} dev questions. No model was called.")
        return
    try:
        stage = FirstStage(args.first_stage, chunks, tracer=tracer(args))
        reranker = make_reranker(args.reranker, tracer=tracer(args))
        selected = select_questions(args, questions)
        if args.eval:
            ideals = {q.id: ideal_gains(q, chunks) for q in selected}
            before, after = {}, {}
            for q in selected:
                run = run_question(q, stage, reranker, depth=args.depth, k=args.depth, model=args.model,
                                   generate=False)
                before[q.id], after[q.id] = run.candidates, run.top
            rows = [("first stage", *metric_row(selected, before, ideals).values()),
                    (f"+ {args.reranker}", *metric_row(selected, after, ideals).values())]
            ui.show_table(f"Dev set · {args.first_stage} depth {args.depth}",
                          ["", "section_recall@3", "evidence_recall@1", "evidence_recall@3", "MRR", "nDCG@3"], rows)
            return
        summary = []
        for number, q in enumerate(selected, start=1):
            ui.show_question(number, len(selected), q.text)
            run = run_question(q, stage, reranker, depth=args.depth, k=args.top_k, model=args.model,
                               think=args.think, tracer=tracer(args))
            ui.show_candidates(run.candidates, q)
            if reranker is not None:
                ui.show_reranked(run.top, q, title=f"Reranked by {args.reranker} · top {args.top_k}")
            if args.show_raw:
                ui.show_raw(render_prompt(args.model, run.messages, think=args.think))
            if run.thinking:
                ui.show_note("Thinking · GENERATIVE MODEL (--think):\n" + run.thinking)
            ui.show_note(f"answer: {run.answer}")
            record = row(run)
            summary.append((q.id, q.category, _first_evidence(record["candidates"]),
                            _first_evidence(record["top"]), "yes" if record["facts"] else "no"))
            if not q.answerable:
                ui.show_note("no-answer question: " + ("refused" if record["refused"] else "FALSE ANSWER"))
        if len(summary) > 1:
            ui.show_table("Summary", ["id", "category", "evidence rank (first stage)",
                                      "evidence rank (after rerank)", "facts"], summary)
    except (OllamaError, RuntimeError) as exc:
        ui.show_error(str(exc))
        raise SystemExit(1) from None


def _first_evidence(records: list[dict]) -> str:
    for position, r in enumerate(records, start=1):
        if r["gain"] == 2:
            return str(position)
    return "-"


def run_two_stages(rerank_fn, file: str) -> None:
    args = parser(f"{Path(file).name}: rerank the first stage's candidates.").parse_args()
    chunks = plant_chunks()
    questions = load_questions(DEV_QUESTIONS)
    try:
        rerank_fn("q", [], lambda q, ps: [], 3)
    except NotImplementedError:
        ui.show_todo("rerank(question, hits, score, k)", "Without it the first-stage order is final.")
        return
    if args.inspect:
        ui.show_note("--inspect: no model was called.")
        return
    try:
        stage = FirstStage(args.first_stage, chunks, tracer=tracer(args))
        reranker = make_reranker(args.reranker if args.reranker != "none" else "fake", tracer=tracer(args))
        selected = select_questions(args, questions)
        candidates = {q.id: stage.candidates(q.text, args.depth) for q in selected}
        mine = {q.id: rerank_fn(q.text, candidates[q.id], reranker.score, args.depth) for q in selected}
    except (OllamaError, RuntimeError) as exc:
        ui.show_error(str(exc))
        raise SystemExit(1) from None
    if not args.eval:
        for number, q in enumerate(selected, start=1):
            ui.show_question(number, len(selected), q.text)
            ui.show_candidates(candidates[q.id], q)
            ui.show_reranked(mine[q.id][: args.top_k], q, title=f"Your rerank() · {reranker.id} · top {args.top_k}")
        return
    ideals = {q.id: ideal_gains(q, chunks) for q in selected}
    ui.show_table(f"Dev set · {args.first_stage} depth {args.depth} · {reranker.id}",
                  ["", "section_recall@3", "evidence_recall@1", "evidence_recall@3", "MRR", "nDCG@3"],
                  [("first stage", *metric_row(selected, candidates, ideals).values()),
                   ("your rerank()", *metric_row(selected, mine, ideals).values())])
    added = [q.id for q in selected if {h.chunk.id for h in mine[q.id]} - {h.chunk.id for h in candidates[q.id]}]
    ui.show_note("Chunks your rerank() added that the first stage never returned: " + (", ".join(added) or "none"))


def run_ndcg(gain_fn, ndcg_fn, file: str) -> None:
    from .metrics import ndcg as library_ndcg

    args = parser(f"{Path(file).name}: graded relevance and nDCG.").parse_args()
    chunks = plant_chunks()
    questions = [q for q in load_questions(DEV_QUESTIONS) if q.answerable]
    try:
        gain_fn(chunks[0], questions[0])
        ndcg_fn([2, 1], [2, 1], 3)
    except NotImplementedError:
        ui.show_todo("gain() / ndcg_at_k()", "Both are needed to score an order.")
        return
    if args.inspect:
        return
    try:
        stage = FirstStage(args.first_stage, chunks, tracer=tracer(args))
        reranker = make_reranker(args.reranker, tracer=tracer(args))
        rows = []
        for q in select_questions(args, questions):
            ideal = sorted((g for g in (gain_fn(c, q) for c in chunks) if g > 0), reverse=True)
            before = stage.candidates(q.text, args.depth)
            after = rerank(q.text, before, reranker, args.depth) if reranker else before
            g_before = [gain_fn(h.chunk, q) for h in before[:3]]
            g_after = [gain_fn(h.chunk, q) for h in after[:3]]
            same_recall = (2 in g_before) == (2 in g_after)
            rows.append((q.id, " ".join(map(str, g_before)), f"{ndcg_fn(g_before, ideal, 3):.3f}",
                         " ".join(map(str, g_after)), f"{ndcg_fn(g_after, ideal, 3):.3f}",
                         "same" if same_recall else "changed",
                         "ok" if abs(ndcg_fn(g_after, ideal, 3) - library_ndcg(after, q, ideal, 3)) < 1e-9 else "differs"))
    except (OllamaError, RuntimeError) as exc:
        ui.show_error(str(exc))
        raise SystemExit(1) from None
    ui.show_table(f"Top 3 gains and nDCG@3 · {args.first_stage} → {args.reranker}",
                  ["id", "gains before", "nDCG@3", "gains after", "nDCG@3", "evidence_recall@3", "vs library"], rows)
    ui.show_note("Rows with 'same' recall and a different nDCG: the reorder changed only the order.")


def run_cross_encoder(score_pair_fn, file: str) -> None:
    import math

    import numpy as np

    from .metrics import gain
    from .rerankers import BGE, MINILM, CrossEncoderReranker

    args = parser(f"{Path(file).name}: (question, passage) -> relevance score.").parse_args()
    spec = BGE if args.reranker == "bge" else MINILM
    encoder = CrossEncoderReranker(spec)
    try:
        encoder._load()
        ui.show_note(f"{spec.repo}@{spec.revision[:12]} · {spec.file} · max_length {spec.max_length} · "
                     f"load {encoder.load_seconds:.2f}s")
        score_pair_fn(encoder._tokenizer, encoder._session, "q", "p")
    except NotImplementedError:
        ui.show_todo("score_pair(tokenizer, session, question, passage)", "The model is loaded; now feed it a pair.")
        return
    except RuntimeError as exc:
        ui.show_error(str(exc))
        raise SystemExit(1) from None
    if args.inspect:
        e = encoder._tokenizer.encode("What is PN-X1Q-199-A?", "Kestrel LX-69 — Spare parts PN-X1Q-199-A: second mirror.")
        ui.show_note("tokens: " + " ".join(e.tokens[:40]))
        ui.show_note("type_ids: " + " ".join(map(str, e.type_ids[:40])) + "   (0 = question, 1 = passage)")
        return

    class Yours:
        id = f"yours/{encoder.id}"

        def score(self, question, passages):
            return [score_pair_fn(encoder._tokenizer, encoder._session, question, p) for p in passages]

    chunks = plant_chunks()
    questions = load_questions(DEV_QUESTIONS)
    try:
        stage = FirstStage(args.first_stage, chunks, tracer=tracer(args))
        selected = select_questions(args, questions)
        before = {q.id: stage.candidates(q.text, args.depth) for q in selected}
        after = {q.id: rerank(q.text, before[q.id], Yours(), args.depth) for q in selected}
    except OllamaError as exc:
        ui.show_error(str(exc))
        raise SystemExit(1) from None
    if not args.eval:
        for number, q in enumerate(selected, start=1):
            ui.show_question(number, len(selected), q.text)
            rows = [(h.first_rank, h.rank, h.chunk.id, f"{h.score:.3f}", f"{h.rerank_score:.2f}",
                     f"{1 / (1 + math.exp(-h.rerank_score)):.3f}", gain(h.chunk, q)) for h in after[q.id][:8]]
            ui.show_table("Cosine (first stage) vs relevance score (cross-encoder)",
                          ["from", "rank", "chunk", "cosine", "logit", "sigmoid", "gain"], rows)
        return
    ideals = {q.id: ideal_gains(q, chunks) for q in selected}
    ui.show_table(f"Dev set · {args.first_stage} depth {args.depth} · your score_pair()",
                  ["", "section_recall@3", "evidence_recall@1", "evidence_recall@3", "MRR", "nDCG@3"],
                  [("first stage", *metric_row(selected, before, ideals).values()),
                   ("+ cross-encoder", *metric_row(selected, after, ideals).values())])
    evidence = [h.rerank_score for q in selected for h in after[q.id] if gain(h.chunk, q) == 2]
    others = [h.rerank_score for q in selected for h in after[q.id] if gain(h.chunk, q) == 0]
    edges = np.linspace(min(evidence + others), max(evidence + others), 11).round(1).tolist()
    edges[-1] += 0.1  # include the maximum
    counts = [(f"{low:.1f} to {high:.1f}", sum(low <= v < high for v in evidence), sum(low <= v < high for v in others))
              for low, high in zip(edges, edges[1:])]
    ui.show_table("Relevance scores (logits) of all candidates", ["logit", "evidence (gain 2)", "irrelevant (gain 0)"],
                  counts)


def run_tev1(exe, file: str) -> None:
    import random
    import time

    from .client import DEFAULT_DECISION_MODEL, decide
    from .scorecache import ScoreCache

    p = parser(f"{Path(file).name}: tev1 as a reranker, mode A and mode B.")
    p.add_argument("--model-decision", default=DEFAULT_DECISION_MODEL, help="Decision model.")
    p.add_argument("--modes", default="A,B,B-reversed,B-shuffled", help="Comma-separated: A, B, B-reversed, B-shuffled.")
    args = p.parse_args()
    try:
        exe.state_a("q", "p"), exe.state_b("q", ["p"]), exe.questions_b(1)
    except NotImplementedError:
        ui.show_todo("state_a / state_b / questions_b", "tev1 needs a state and questions.")
        return
    where = "local CPU" if "127.0.0.1" in ollama_url() or "localhost" in ollama_url() else f"remote {ollama_url()}"
    ui.show_note(f"Ollama: {ollama_url()} ({where}). Times measured here are {where} times.")
    if args.inspect:
        ui.show_raw(exe.state_a("What is PN-X1Q-199-A?", "Spare parts PN-X1Q-199-A: second mirror."), "state, mode A")
        ui.show_raw(exe.state_b("What is PN-X1Q-199-A?", ["first passage", "second passage"]), "state, mode B")
        return
    cache = ScoreCache()

    class Student:
        def __init__(self, mode, order):
            self.mode, self.order, self.requests = mode, order, 0
            self.id = f"yours/tev1:{args.model_decision}/{mode}/{order}"

        def score(self, question, passages):
            if self.mode == "A":
                out = []
                for passage in passages:
                    parts = [self.id, str(exe.QUESTION_A), question, passage]
                    value = cache.get(parts)
                    if value is None:
                        self.requests += 1
                        value = decide(args.model_decision, exe.state_a(question, passage), exe.QUESTION_A,
                                       tracer=tracer(args)).answers
                        value = float(next(iter(value.values()))["noul"])
                        cache.put(parts, value)
                    out.append(value)
                return out
            positions = list(range(len(passages)))
            if self.order == "reversed":
                positions.reverse()
            elif self.order == "shuffled":
                random.Random(0).shuffle(positions)
            shown = [passages[i] for i in positions]
            parts = [self.id, str(exe.questions_b(len(shown))), question, *shown]
            scores = cache.get(parts)
            if scores is None:
                self.requests += 1
                answers = decide(args.model_decision, exe.state_b(question, shown), exe.questions_b(len(shown)),
                                 tracer=tracer(args)).answers
                scores = [float(answers[f"p{j}"]["noul"]) for j in range(1, len(shown) + 1)]
                cache.put(parts, scores)
            out = [0.0] * len(passages)
            for shown_index, original in enumerate(positions):
                out[original] = scores[shown_index]
            return out

    chunks = plant_chunks()
    questions = load_questions(DEV_QUESTIONS)
    modes = [m.strip() for m in args.modes.split(",")]
    try:
        stage = FirstStage(args.first_stage, chunks, tracer=tracer(args))
        selected = select_questions(args, questions)
        before = {q.id: stage.candidates(q.text, args.depth) for q in selected}
        ideals = {q.id: ideal_gains(q, chunks) for q in selected}
        rows = [("first stage", *metric_row(selected, before, ideals).values(), 0, "-")]
        for mode in modes:
            reranker = Student(mode[0], mode.split("-", 1)[1] if "-" in mode else "original")
            started = time.perf_counter()
            after = {q.id: rerank(q.text, before[q.id], reranker, args.depth) for q in selected}
            seconds = time.perf_counter() - started
            per_q = f"{seconds / len(selected):.1f}" if reranker.requests else "cached"
            rows.append((f"tev1 {mode}", *metric_row(selected, after, ideals).values(), reranker.requests, per_q))
            if not args.eval:
                for q in selected:
                    ui.show_reranked(after[q.id][: args.top_k], q, title=f"tev1 {mode} · {q.id}")
    except OllamaError as exc:
        ui.show_error(str(exc))
        raise SystemExit(1) from None
    ui.show_table(f"{args.first_stage} depth {args.depth} · {args.model_decision} · {where}",
                  ["", "section_recall@3", "evidence_recall@1", "evidence_recall@3", "MRR", "nDCG@3",
                   "requests", "s/question"], rows)


def run_depth(depth_curve_fn, file: str) -> None:
    args = parser(f"{Path(file).name}: candidate depth and the ceiling.").parse_args()
    depths = [5, 10, 20, 50]
    chunks = plant_chunks()
    questions = load_questions(DEV_QUESTIONS)
    try:
        depth_curve_fn([], {}, lambda q, hits: hits, [5], {})
    except NotImplementedError:
        ui.show_todo("depth_curve(...)", "One row per depth: the ceiling, before, after.")
        return
    except ValueError:
        pass  # an empty question list may raise in the metrics; the function exists
    if args.inspect:
        return
    stages = [args.first_stage] + (["fake"] if args.first_stage != "fake" else [])
    try:
        reranker = make_reranker(args.reranker, tracer=tracer(args))
        ideals = {q.id: ideal_gains(q, chunks) for q in questions}
        for name in stages:
            stage = FirstStage(name, chunks, tracer=tracer(args))
            candidates = {q.id: stage.candidates(q.text, max(depths)) for q in questions}
            curve = depth_curve_fn(questions, candidates, lambda q, hits: rerank(q.text, hits, reranker, len(hits)),
                                   depths, ideals)
            ui.show_table(f"{name} → {reranker.id}",
                          ["depth N", "ceiling: evidence_recall@N", "first stage @1", "reranked @1", "nDCG@3 after"],
                          [(r["depth"], r["ceiling"], r["first_stage@1"], r["reranked@1"], r["nDCG@3"]) for r in curve])
    except (OllamaError, RuntimeError) as exc:
        ui.show_error(str(exc))
        raise SystemExit(1) from None
    ui.show_note("reranked @1 can never exceed the ceiling: the reranker only reorders what the first stage found.")


def run_cost(pick_fn, file: str) -> None:
    from .costs import MEASUREMENTS, load_timing, save_timing, time_cross_encoder
    from .metrics import evidence_recall_at_k, mean_ndcg
    from .rerankers import BGE, MINILM, Tev1Reranker
    from .scorecache import ScoreCache

    class CacheOnly(ScoreCache):
        def get(self, parts):
            value = super().get(parts)
            if value is None:
                raise LookupError("not cached")
            return value

    p = parser(f"{Path(file).name}: cost versus quality, under a CPU budget.")
    p.add_argument("--budget", type=float, default=1.0, help="CPU seconds per question for the reranker.")
    args = p.parse_args()
    try:
        pick_fn([], 1.0)
    except NotImplementedError:
        ui.show_todo("pick_config(rows, budget_s)", "The table is built; now choose from it.")
        return
    if args.inspect:
        return
    chunks = plant_chunks()
    questions = load_questions(DEV_QUESTIONS)
    answerable_qs = [q for q in questions if q.answerable]
    ideals = {q.id: ideal_gains(q, chunks) for q in questions}
    timings = {}
    rows = []
    try:
        for stage_name in ("nomic", "bm25"):
            stage = FirstStage(stage_name, chunks, tracer=tracer(args))
            full = {q.id: stage.candidates(q.text, 50) for q in questions}
            for depth in (10, 20, 50):
                cut = {qid: hits[:depth] for qid, hits in full.items()}
                items = [(q.text, [h.chunk.text for h in cut[q.id]]) for q in answerable_qs]
                for name in ("none", "minilm", "bge", "tev1-a"):
                    if name == "tev1-a" and depth == 50:
                        continue  # 50 tev1 requests per question: out of any CPU budget here
                    # tev1 quality comes from the score cache filled by EXE04: no tev1 request on the CPU here.
                    reranker = Tev1Reranker(cache=CacheOnly()) if name == "tev1-a" else make_reranker(name)
                    try:
                        after = {q.id: rerank(q.text, cut[q.id], reranker, depth) if reranker else cut[q.id]
                                 for q in questions}
                    except LookupError:
                        ui.show_note(f"{stage_name} N={depth} tev1-a: quality not cached; "
                                     + TEV1_FILL_HINT.format(depth=depth) + f" --first-stage {stage_name}")
                        continue
                    if name == "none":
                        cost = 0.0
                    elif name in ("minilm", "bge"):
                        spec = MINILM if name == "minilm" else BGE
                        if (name, depth) not in timings:
                            timings[(name, depth)] = time_cross_encoder(spec, items[:8])
                            if depth == 20:  # EXE08 reads the cost per pair from this file
                                save_timing(timings[(name, depth)], MEASUREMENTS / f"{name}-cpu.json")
                        cost = timings[(name, depth)].s_per_question
                    else:
                        measured = load_timing(MEASUREMENTS / "tev1-A-cpu.json")
                        cost = round(measured.seconds / measured.pairs * depth, 1) if measured else float("inf")
                    rows.append({"config": f"{stage_name} · N={depth} · {name}",
                                 "evidence_recall@1": evidence_recall_at_k(answerable_qs, after, 1),
                                 "nDCG@3": mean_ndcg(answerable_qs, after, ideals, 3), "s/question": cost})
    except (OllamaError, RuntimeError) as exc:
        ui.show_error(str(exc))
        raise SystemExit(1) from None
    ui.show_table("Dev set · quality and CPU cost of the reranker per question",
                  ["config", "evidence_recall@1", "nDCG@3", "s/question (CPU)"],
                  [(r["config"], r["evidence_recall@1"], r["nDCG@3"],
                    "not measured" if r["s/question"] == float("inf") else r["s/question"]) for r in rows])
    batch = time_cross_encoder(MINILM, [(q.text, [h.chunk.text for h in FirstStage("bm25", chunks).candidates(q.text, 20)])
                                        for q in answerable_qs[:8]], batch=8)
    ui.show_note(f"MiniLM batch 8: {batch.ms_per_pair} ms/pair (batch 1: "
                 f"{timings[('minilm', 20)].ms_per_pair} ms/pair). Model load: {batch.load_seconds:.2f}s, not counted.")
    choice = pick_fn(rows, args.budget)
    ui.show_note(f"your pick_config(budget {args.budget}s): " + (choice["config"] if choice else "nothing fits"))


ROWS_DIR = Path(__file__).resolve().parents[2] / "exercises" / "exe07-diagnosis" / "rows"


def run_diagnosis(diagnose_fn, file: str) -> None:
    import json

    rows = []
    for path in sorted(ROWS_DIR.glob("*.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        try:
            found = diagnose_fn(record)
        except NotImplementedError:
            ui.show_todo("diagnose(row)", "Read one row in rows/ by hand first.")
            return
        evidence_rank = next((str(c["first_rank"]) for c in record["candidates"] if c["gain"] == 2), "-")
        rows.append((path.stem, record["settings"]["depth"], record["settings"]["top_k"], evidence_rank,
                     found, record["expected"], "✓" if found == record["expected"] else "✗"))
    ui.show_table("First failing stage", ["row", "N", "k", "evidence first rank", "yours", "expected", ""], rows)


def run_benchmark(file: str) -> None:
    import json

    from .benchmark import diagnose
    from .corpus import HOLDOUT_QUESTIONS
    from .costs import MEASUREMENTS, is_local

    p = parser(f"{Path(file).name}: three pipelines on the holdout.", generation=True)
    p.add_argument("--pipeline", choices=["embedding", "tev1", "minilm"], default="minilm")
    p.add_argument("--compare", action="store_true", help="Print the table of the saved runs.")
    args = p.parse_args()
    results_dir = MEASUREMENTS / "exe08"
    if args.compare:
        compare_benchmarks(results_dir)
        return
    questions = load_questions(HOLDOUT_QUESTIONS)
    reranker_name = {"embedding": "none", "tev1": "tev1-a", "minilm": "minilm"}[args.pipeline]
    where = "CPU" if is_local() else f"GPU ({ollama_url()})"
    ui.show_note(f"holdout · {args.first_stage} depth {args.depth} · {args.pipeline} · top {args.top_k} · "
                 f"generator {args.model} · Ollama {where}")
    if args.inspect:
        return
    try:
        stage = FirstStage(args.first_stage, plant_chunks(), tracer=tracer(args))
        reranker = make_reranker(reranker_name, tracer=tracer(args))
        if hasattr(reranker, "spec"):
            ui.show_note(f"cross-encoder: {reranker.spec}")
        selected = select_questions(args, questions)
        records = []
        for number, q in enumerate(selected, start=1):
            ui.show_question(number, len(selected), q.text)
            run = run_question(q, stage, reranker, depth=args.depth, k=args.top_k, model=args.model,
                               think=args.think, tracer=tracer(args))
            record = row(run) | {"where": where}
            record["diagnosis"] = diagnose(record)
            ui.show_reranked(run.top, q, title=f"top {args.top_k} · {args.pipeline}")
            ui.show_note(f"answer: {run.answer}  ·  first failing stage: {record['diagnosis']}")
            records.append(record)
    except (OllamaError, RuntimeError) as exc:
        ui.show_error(str(exc))
        raise SystemExit(1) from None
    if args.eval:
        results_dir.mkdir(parents=True, exist_ok=True)
        path = results_dir / f"{args.first_stage}-{args.pipeline}.json"
        path.write_text(json.dumps(records, indent=1, ensure_ascii=False))
        compare_benchmarks(results_dir)


def compare_benchmarks(results_dir: Path) -> None:
    import json

    from .corpus import HOLDOUT_QUESTIONS
    from .costs import reranker_cpu_seconds
    from .metrics import abstention_accuracy, dcg, false_answer_rate

    chunks = plant_chunks()
    questions = {q.id: q for q in load_questions(HOLDOUT_QUESTIONS)}
    ideals = {qid: ideal_gains(q, chunks) for qid, q in questions.items()}
    retrieval, answers_table, cost = [], [], []
    for path in sorted(results_dir.glob("*.json")):
        records = json.loads(path.read_text())
        qs = [questions[r["question_id"]] for r in records]
        ans = [r for r in records if r["answerable"]]
        top_gains = {r["question_id"]: [c["gain"] for c in r["top"]] for r in ans}

        def evidence_at(k):
            return sum(2 in g[:k] for g in top_gains.values()) / len(ans)

        mrr_value = sum(1 / (g.index(2) + 1) if 2 in g else 0.0 for g in top_gains.values()) / len(ans)
        ndcg_value = sum(dcg(g, 3) / dcg(ideals[qid], 3) if dcg(ideals[qid], 3) else 0.0
                         for qid, g in top_gains.items()) / len(ans)
        answers = {r["question_id"]: r["answer"] for r in records}
        measured_here = sum(r["seconds"]["rerank"] for r in records) / len(records)
        seconds_cpu = reranker_cpu_seconds(path.stem.split("-", 1)[1], records)
        cpu = "not measured" if seconds_cpu is None else f"{seconds_cpu:.2f}"
        retrieval.append((path.stem, f"{evidence_at(1):.2f}", f"{evidence_at(3):.2f}", f"{mrr_value:.2f}",
                          f"{ndcg_value:.2f}"))
        answers_table.append((path.stem, f"{sum(r['facts'] for r in ans)}/{len(ans)}",
                              f"{sum(r['citations_ok'] for r in records)}/{len(records)}",
                              f"{false_answer_rate(qs, answers):.2f}", f"{abstention_accuracy(qs, answers):.2f}"))
        cost.append((path.stem, f"{sum(r['rerank_requests'] for r in records) / len(records):.0f}", cpu,
                     f"{measured_here:.2f}", records[0]["where"].split(" ")[0]))
    ui.show_table("Holdout · retrieval and reranking",
                  ["run", "evidence_recall@1", "evidence_recall@3", "MRR@3", "nDCG@3"], retrieval)
    ui.show_table("Holdout · answers (code checks)",
                  ["run", "facts", "citations ok", "false_answer_rate", "abstention_accuracy"], answers_table)
    ui.show_table("Holdout · reranker cost per question",
                  ["run", "requests (cache on)", "s CPU", "s this run (cache on)", "where"], cost)
    ui.show_note("MRR@3 uses the first evidence chunk within the top 3 the generator reads. "
                 "'this run' times use the score cache: the CPU costs come from EXE06.")
