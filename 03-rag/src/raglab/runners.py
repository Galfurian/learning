"""The run loop of each exercise. An exercise file passes its own pieces in."""

import json
from collections.abc import Callable
from pathlib import Path

import numpy as np

from . import ui
from .chunking import chunk_section as library_chunk_section
from .client import OllamaError, render_prompt
from .context import build_context
from .corpus import DEV_MANUALS, load_manuals
from .embedders import FakeEmbedder
from .evalset import (
    by_category,
    evidence_at_k,
    first_relevant_rank,
    load_questions,
    mrr,
    recall_at_k,
    run_search,
)
from .exercise import (
    dev_chunks,
    dev_index,
    make_embedder,
    make_search,
    parser,
    select_questions,
    tracer,
)
from .generation import SYSTEM_PROMPT, answer_ok, check_citations
from .hybrid import idf
from .index import Hit, Index
from .pipeline import ContextBuilder, answer_question, trace_record

RAG_ACTORS = [
    ("APP", "The exercise file and src/raglab: chunks, searches, builds the context, checks the answer."),
    ("EMBEDDING MODEL", "POST /api/embed: text -> vector. It never sees the question and the manuals together."),
    ("GENERATIVE MODEL", "POST /api/chat: question + context -> answer. It reads only what the APP gives it."),
]


def run_rag(
    file: str,
    *,
    system_prompt: str = SYSTEM_PROMPT,
    check: Callable = check_citations,
    context_builder: ContextBuilder = build_context,
    min_score: float | None = None,
) -> None:
    args = parser(f"{Path(file).name}: retrieve, build the context, generate, check.", generation=True).parse_args()
    if args.verbose:
        ui.show_actors(RAG_ACTORS)
    chunks = dev_chunks(args)
    if args.inspect:
        ui.show_chunks(chunks, limit=20)
        ui.show_note("--inspect: no model was called.")
        ui.show_raw(system_prompt, title="System prompt · before the chat template")
        return
    effective_min_score = min_score if min_score is not None else args.min_score
    try:
        index = dev_index(args, chunks)
        questions = select_questions(args, load_questions())
        search = make_search(args, index)
        rows = []
        for number, question in enumerate(questions, start=1):
            ui.show_question(number, len(questions), question.text)
            trace = answer_question(
                question.text, search, k=args.top_k, budget=args.budget,
                min_score=effective_min_score,
                model=args.model, think=args.think, system_prompt=system_prompt,
                context_builder=context_builder, tracer=tracer(args),
            )
            trace.citations = check(trace.answer, trace.context.ids)
            ui.show_hits(trace.hits, question.relevant)
            ui.show_context(trace.context, trace.abstain_reason)
            if args.show_raw and not trace.abstained:
                ui.show_raw(render_prompt(args.model, trace.messages, think=args.think))
            ui.show_answer(trace)
            if args.record:
                folder = Path(args.record)
                folder.mkdir(parents=True, exist_ok=True)
                settings = {"embedder": index.embedder.name, "k": args.top_k, "budget": args.budget,
                            "min_score": effective_min_score, "model": args.model, "size": args.size,
                            "retriever": getattr(args, "retriever", "semantic")}
                (folder / f"{question.id}.json").write_text(
                    json.dumps(trace_record(trace, question, settings), indent=1, ensure_ascii=False))
            rows.append((question.id, question.category, " ".join(trace.answer.split())[:60],
                         "ok" if trace.citations.ok else trace.citations.problem,
                         "yes" if answer_ok(trace.answer, question) else "no" if question.category != "free" else "-"))
        if len(rows) > 1:
            ui.show_table("Summary", ["id", "category", "answer", "citations", "facts"], rows)
            ui.show_note("facts: checked by code (expected strings present, or a refusal for no-answer questions). "
                         "A 'yes' does not prove the cited chunk supports the claim.")
    except OllamaError as exc:
        ui.show_error(str(exc))
        raise SystemExit(1) from None


def run_embeddings(pairs, normalize, file: str) -> None:
    args = parser(f"{Path(file).name}: texts become vectors.", evaluation=False).parse_args()
    raw = FakeEmbedder(normalized=False)
    first = pairs[0][0]
    ui.console.rule("[bold]FakeEmbedder: hashed word counts")
    ui.show_vector(f"raw   {first!r}", raw.embed_query(first))
    try:
        ui.show_vector("normalize()", normalize(raw.embed_query(first)))
        fake_scores = [float(normalize(raw.embed_query(a)) @ normalize(raw.embed_query(b))) for a, b, _ in pairs]
    except NotImplementedError:
        ui.show_todo("normalize(vector)", "Without it the fake vectors are raw counts: their dot product is not a cosine.")
        fake_scores = [float("nan")] * len(pairs)
    if args.inspect:
        ui.show_note("--inspect: the embedding model was not called.")
        return
    try:
        real = make_embedder(args)
        ui.console.rule(f"[bold]EMBEDDING MODEL: {real.name}")
        vectors = real.embed_documents([t for a, b, _ in pairs for t in (a, b)])
    except OllamaError as exc:
        ui.show_error(str(exc))
        raise SystemExit(1) from None
    ui.show_vector(f"{real.name} {first!r}", vectors[0])
    rows = []
    for i, (a, b, label) in enumerate(pairs):
        va, vb = vectors[2 * i], vectors[2 * i + 1]
        cos = float(va @ vb / (np.linalg.norm(va) * np.linalg.norm(vb)))
        rows.append((f"{a} | {b}", label, fake_scores[i], cos, float(va @ vb)))
    ui.show_table("Pairs", ["pair", "label", "fake cosine", "real cosine", "real dot"], rows)
    ui.show_note("The real vectors have norm 1, so the cosine and the dot product are the same number.")


def _ranked(top_k, query_vector, vectors, chunks, k) -> list[Hit]:
    by_id = {c.id: c for c in chunks}
    return [Hit(by_id[cid], score, rank) for rank, (cid, score) in
            enumerate(top_k(query_vector, vectors, [c.id for c in chunks], k), start=1)]


def run_ranking(cosine, top_k, file: str) -> None:
    args = parser(f"{Path(file).name}: rank chunks by cosine.").parse_args()
    chunks = dev_chunks(args)
    questions = select_questions(args, load_questions())
    try:
        cosine(np.ones(2), np.ones(2))
        top_k(np.ones(2), np.ones((1, 2)), ["x"], 1)
    except NotImplementedError:
        ui.show_todo("cosine() / top_k()", "Both are needed to rank the chunks.")
        return
    if args.inspect:
        ui.show_chunks(chunks, limit=20)
        return
    real = make_embedder(args)
    embedders = [FakeEmbedder(), real] if args.eval and not args.fake_embed else [real]
    try:
        runs = []
        for embedder in embedders:
            vectors = embedder.embed_documents([c.text for c in chunks], [c.title for c in chunks])
            results = {q.id: _ranked(top_k, embedder.embed_query(q.text), vectors, chunks, max(args.top_k, 10)) for q in questions}
            runs.append((embedder.name, results))
    except OllamaError as exc:
        ui.show_error(str(exc))
        raise SystemExit(1) from None
    if not args.eval:
        name, results = runs[-1]
        for number, q in enumerate(questions, start=1):
            ui.show_question(number, len(questions), q.text)
            ui.show_hits(results[q.id][: args.top_k], q.relevant, title=f"Ranked by your top_k() · {name}", show_text=True)
        return
    columns = ["id", "category"] + [f"{name} rank" for name, _ in runs] + [f"{name} top-1 score" for name, _ in runs]
    rows = []
    for q in questions:
        ranks = [first_relevant_rank(r[q.id], q.relevant) or "-" if q.answerable else "n/a" for _, r in runs]
        tops = [r[q.id][0].score for _, r in runs]
        rows.append([q.id, q.category, *ranks, *tops])
    ui.show_table("Rank of the first relevant chunk", columns, rows)
    for name, results in runs:
        ui.show_note(f"{name}: R@1 {recall_at_k(questions, results, 1):.2f}  R@3 {recall_at_k(questions, results, 3):.2f}")


def run_chunking(chunker, file: str, sizes=(15, 30, 60, 120, 400)) -> None:
    args = parser(f"{Path(file).name}: sections -> chunks.", evaluation=False).parse_args()
    sections = load_manuals(DEV_MANUALS)
    try:
        sample = chunker(next(s for s in sections if s.id == "lx40-errors"), args.size, args.overlap)
    except NotImplementedError:
        ui.show_todo("chunk_section(section, size, overlap)", "Without chunks there is nothing to embed.")
        return
    ui.show_chunks(sample)
    if args.inspect:
        ui.show_note(f"--inspect: lx40-errors with size={args.size}, overlap={args.overlap}. No model was called.")
        return
    questions = load_questions()
    rows = []
    try:
        embedder = make_embedder(args)
        configs = [(f"yours, size {size}", lambda s, size=size: chunker(s, size, min(args.overlap, size // 4))) for size in sizes]
        configs.append((f"library, size {args.size}, no title",
                        lambda s: library_chunk_section(s, args.size, args.overlap, with_title=False)))
        for label, make in configs:
            chunks = [c for s in sections for c in make(s)]
            index = Index.build(chunks, embedder)
            results = run_search(questions, index.search, 10)
            words = sum(len(c.text.split()) for c in chunks) / len(chunks)
            rows.append((label, len(chunks), round(words), recall_at_k(questions, results, 1),
                         evidence_at_k(questions, results, 1), recall_at_k(questions, results, 3),
                         evidence_at_k(questions, results, 3)))
    except OllamaError as exc:
        ui.show_error(str(exc))
        raise SystemExit(1) from None
    ui.show_table(f"Chunking vs retrieval · {embedder.name}",
                  ["chunker", "chunks", "words/chunk", "R@1", "E@1", "R@3", "E@3"], rows)
    ui.show_note("R@k: a chunk of a relevant section is in the top k. "
                 "E@k: the top k chunks contain the facts a correct answer needs.")


def run_retrieval(search, recall, file: str) -> None:
    args = parser(f"{Path(file).name}: the index and the eval set.").parse_args()
    if args.inspect:
        ui.show_chunks(dev_chunks(args), limit=20)
        return
    questions = load_questions()
    try:
        index = dev_index(args)
        query_vectors = {q.id: index.embedder.embed_query(q.text) for q in select_questions(args, questions)}
    except OllamaError as exc:
        ui.show_error(str(exc))
        raise SystemExit(1) from None
    try:
        results = {qid: search(index.vectors, index.chunks, v, 10) for qid, v in query_vectors.items()}
    except NotImplementedError:
        ui.show_todo("search(vectors, chunks, query, k)", "The index exists, but nothing searches it yet.")
        return
    if not args.eval:
        for number, q in enumerate(select_questions(args, questions), start=1):
            ui.show_question(number, len(query_vectors), q.text)
            ui.show_hits(results[q.id][: args.top_k], q.relevant, show_text=True)
        return
    try:
        mine = [recall(questions, results, k) for k in (1, 3, 5)]
    except NotImplementedError:
        ui.show_todo("recall_at_k(questions, results, k)", "Search works; now measure it.")
        return
    reference = [recall_at_k(questions, results, k) for k in (1, 3, 5)]
    ui.show_table(f"Retrieval on the dev set · {index.embedder.name} · size {args.size}",
                  ["metric", "your recall_at_k", "raglab.evalset"],
                  [(f"R@{k}", m, r) for k, m, r in zip((1, 3, 5), mine, reference)]
                  + [("MRR", "", mrr(questions, results)), ("E@3", "", evidence_at_k(questions, results, 3))])
    ui.show_table("R@3 by category", ["category", "found", "answerable"],
                  [(c, f, t) for c, (f, t) in sorted(by_category(questions, results, 3).items())])
    misses = [(q.id, q.category, first_relevant_rank(results[q.id], q.relevant) or ">10",
               ", ".join(h.chunk.id for h in results[q.id][:3]))
              for q in questions if q.answerable and not (first_relevant_rank(results[q.id], q.relevant) or 99) <= 3]
    ui.show_table("Misses at k=3", ["id", "category", "rank", "top 3"], misses)


def threshold_table(top1, cost_miss: float, cost_false: float):
    candidates = [0.0] + sorted({round(score, 3) for score, _ in top1})
    rows = []
    for threshold in candidates:
        missed = sum(answerable and score < threshold for score, answerable in top1)
        passed = sum(not answerable and score >= threshold for score, answerable in top1)
        rows.append((threshold, missed, passed, cost_miss * missed + cost_false * passed))
    return rows


def run_context(build_context_fn, answerable, file: str, *, threshold: float, cost_miss: float, cost_false: float) -> None:
    args = parser(f"{Path(file).name}: hits -> context, and when to abstain.", generation=True).parse_args()
    questions = load_questions()
    try:
        index = dev_index(args)
        results = run_search(questions, index.search, args.top_k)
    except OllamaError as exc:
        ui.show_error(str(exc))
        raise SystemExit(1) from None
    top1 = [(results[q.id][0].score, q.answerable) for q in questions]
    scores = [s for s, _ in top1]
    low, high = round(min(scores) - 0.05, 1), round(max(scores) + 0.05, 1)
    bins = [round(low + 0.05 * i, 2) for i in range(round((high - low) / 0.05) + 1)]
    ui.show_histogram({"answerable": [s for s, a in top1 if a], "no answer": [s for s, a in top1 if not a]}, bins)
    worst = min(s for s, a in top1 if a)
    best_none = max(s for s, a in top1 if not a)
    ui.show_note(f"lowest answerable top-1 {worst:.3f} · highest no-answer top-1 {best_none:.3f} · "
                 + ("the groups OVERLAP: no threshold separates them" if best_none >= worst else "separable on this set"))
    rows = threshold_table(top1, cost_miss, cost_false)
    best = min(rows, key=lambda r: (r[3], r[0]))
    mine = next((r for r in rows if r[0] >= threshold), rows[-1])
    ui.show_table(f"Thresholds · cost: missed answer {cost_miss}, wrong accept {cost_false}",
                  ["threshold", "answerable refused", "no-answer passed", "cost"],
                  [r for r in rows if r in (best, mine) or r[0] == 0.0])
    ui.show_note(f"cheapest threshold on this dev set: {best[0]:.3f}. Yours: {threshold}. "
                 f"Only {sum(not a for _, a in top1)} no-answer questions: this choice rests on very little data.")
    selected = select_questions(args, questions)
    for number, q in enumerate(selected, start=1):
        hits = results[q.id] if q.id in results else index.search(q.text, args.top_k)
        try:
            keep = answerable(hits)
            context = build_context_fn(hits, args.budget)
        except NotImplementedError:
            ui.show_todo("build_context(hits, budget) / answerable(hits)", "The histogram is above; now write the policy.")
            return
        ui.show_question(number, len(selected), q.text)
        ui.show_hits(hits, q.relevant)
        ui.show_note(f"answerable(hits) -> {keep}" + ("" if keep else ": the APP would abstain, no generator call"))
        if keep:
            ui.show_context(context)


def run_hybrid(keyword_search, fuse, file: str) -> None:
    args = parser(f"{Path(file).name}: semantic + keyword search.").parse_args()
    questions = load_questions()
    chunks = dev_chunks(args)
    weights = idf(chunks)
    try:
        keyword_search(chunks, weights, "PN-77A", 1)
    except NotImplementedError:
        ui.show_todo("keyword_search(chunks, weights, query, k)", "Only the semantic retriever exists so far.")
        return
    try:
        index = dev_index(args, chunks)
    except OllamaError as exc:
        ui.show_error(str(exc))
        raise SystemExit(1) from None
    depth = 10
    semantic = run_search(questions, index.search, depth)
    keyword = {q.id: keyword_search(chunks, weights, q.text, depth) for q in questions}
    try:
        fused = {q.id: fuse([semantic[q.id], keyword[q.id]]) for q in questions}
    except NotImplementedError:
        ui.show_todo("fuse(rankings)", "Keyword search works; now combine it with the semantic ranking.")
        fused = None
    runs = [("semantic", semantic), ("keyword", keyword)] + ([("fused", fused)] if fused else [])
    if not args.eval:
        for number, q in enumerate(select_questions(args, questions), start=1):
            ui.show_question(number, len(questions), q.text)
            for name, results in runs:
                ui.show_hits(results[q.id][: args.top_k], q.relevant, title=name, show_text=True)
        return
    categories = sorted({q.category for q in questions if q.answerable})
    rows = []
    for name, results in runs:
        table = by_category(questions, results, args.top_k)
        rows.append([name, recall_at_k(questions, results, args.top_k), evidence_at_k(questions, results, args.top_k),
                     *(f"{table[c][0]}/{table[c][1]}" for c in categories)])
    ui.show_table(f"R@{args.top_k} · {index.embedder.name}", ["retriever", "R@k", "E@k", *categories], rows)


def run_diagnosis(diagnose, file: str) -> None:
    folder = Path(file).resolve().parent / "traces"
    rows = []
    for path in sorted(folder.glob("*.json")):
        trace = json.loads(path.read_text(encoding="utf-8"))
        try:
            found = diagnose(trace)
        except NotImplementedError:
            ui.show_todo("diagnose(trace)", "Read one trace in traces/ by hand first.")
            return
        rows.append((path.stem, trace["question"][:50], ", ".join(h["id"] for h in trace["hits"][:3]),
                     ", ".join(c["id"] for c in trace["context"]) or "-", found, trace.get("expected", "?"),
                     "✓" if found == trace.get("expected") else "✗"))
    ui.show_table("First point of failure", ["trace", "question", "top hits", "context", "yours", "expected", ""], rows)
