"""EXE09 — a solved demo: plant manuals larger than the context, three ways to answer.

--mode stuff     the APP puts as many whole manuals as fit (unit 01 EXE05, at scale)
--mode pipeline  the APP always retrieves, then the generator answers (EXE01–EXE07)
--mode tool      the generator calls the MCP tool search_manuals when and how it wants
--eval           the holdout set, scored by code; one mode per run (WSL rule)
--compare        the table of the saved --eval runs
"""

import asyncio
import json
import sys
import time
from pathlib import Path

import config

from raglab import ui
from raglab.agent import run_tool_agent
from raglab.cache import UNIT_ROOT, EmbeddingCache
from raglab.chunking import chunk_all, chunk_section
from raglab.client import OllamaError, chat
from raglab.context import build_context, estimate_tokens
from raglab.corpus import PLANT_HOLDOUT, PLANT_MANUALS, load_manuals
from raglab.embedders import OllamaEmbedder
from raglab.evalset import first_relevant_rank, load_questions
from raglab.exercise import parser, select_questions, tracer
from raglab.generation import answer_ok, build_messages, check_citations
from raglab.hybrid import BM25, HybridSearch
from raglab.index import Hit, Index
from raglab.pipeline import answer_question

HERE = Path(__file__).resolve().parent
RESULTS = UNIT_ROOT / ".cache" / "measurements"


def stuffed_context(sections):
    """Whole sections, in file order, until STUFF_BUDGET is used. The rest is never seen."""
    hits = [Hit(chunk_section(s, size=100_000, overlap=0)[0], 0.0, rank) for rank, s in enumerate(sections, start=1)]
    return build_context(hits, config.STUFF_BUDGET)


def run_one(mode, question, args, sections, chunks, search):
    started = time.perf_counter()
    if mode == "stuff":
        context = stuffed_context(sections)
        result = chat(args.model, build_messages(question.text, context), num_ctx=config.NUM_CTX,
                      think=args.think, tracer=tracer(args))
        seen = [Hit(c, 0.0, r) for r, c in enumerate(context.chunks, start=1)]
        answer, citations, tokens = result.content, check_citations(result.content, context.ids), result.prompt_tokens
        thinking = result.thinking
        extra = f"{len(context.chunks)} of {len(sections)} sections fit"
    elif mode == "pipeline":
        trace = answer_question(question.text, search, k=config.K, budget=config.BUDGET, min_score=config.MIN_SCORE,
                                model=args.model, num_ctx=config.NUM_CTX, think=args.think, tracer=tracer(args))
        seen, answer, citations, tokens = trace.hits, trace.answer, trace.citations, trace.prompt_tokens
        thinking = trace.thinking
        extra = "abstained: " + trace.abstain_reason if trace.abstained else ""
    else:
        run = asyncio.run(run_tool_agent(question.text, HERE / "manual_server.py", model=args.model,
                                         num_ctx=config.NUM_CTX, think=args.think, tracer=tracer(args)))
        by_id = {c.id: c for c in chunks}
        seen = [Hit(by_id[s["id"]], s["score"], r) for r, s in enumerate(run.seen, start=1) if s["id"] in by_id]
        answer, citations, tokens = run.answer, run.citations, run.prompt_tokens
        thinking = run.thinking
        extra = f"searches: {run.searches}"
    return {
        "id": question.id, "category": question.category, "answer": answer,
        # A chunk of a relevant section reached the generator. (has_evidence() is too loose here:
        # short values such as "88" also appear in other manuals of the plant.)
        "evidence": first_relevant_rank(seen, question.relevant) is not None if question.answerable else None,
        "seen": [h.chunk.id for h in seen][:50],
        "facts": answer_ok(answer, question), "citations": citations.ok,
        "prompt_tokens": tokens, "seconds": round(time.perf_counter() - started, 1), "note": extra,
        "thinking": thinking,
    }


def compare() -> None:
    rows = []
    order = {"stuff": 0, "pipeline": 1, "tool": 3}
    for path in sorted(RESULTS.glob("exe09-*.json"), key=lambda p: order.get(p.stem[6:], 2)):
        mode = path.stem[6:]
        runs = json.loads(path.read_text())
        answerable = [r for r in runs if r["evidence"] is not None]
        rows.append((mode, len(runs),
                     f"{sum(r['evidence'] for r in answerable)}/{len(answerable)}",
                     f"{sum(r['facts'] for r in runs)}/{len(runs)}",
                     f"{sum(r['citations'] for r in runs)}/{len(runs)}",
                     round(sum(r["prompt_tokens"] for r in runs) / len(runs)),
                     round(sum(r["seconds"] for r in runs) / len(runs), 1)))
    ui.show_table("Holdout · scored by code", ["mode", "questions", "evidence seen", "facts", "citations ok",
                                                "avg prompt tokens", "avg s"], rows)


def main() -> None:
    p = parser("EXE09: plant manuals, three modes, holdout verification.", generation=True)
    p.add_argument("--mode", choices=["stuff", "pipeline", "tool"], default="pipeline")
    p.add_argument("--compare", action="store_true", help="Print the table of saved --eval runs.")
    args = p.parse_args()
    if args.compare:
        compare()
        return
    sections = load_manuals(PLANT_MANUALS)
    total = sum(estimate_tokens(s.text) for s in sections)
    ui.show_note(f"{len(sections)} sections, about {total} tokens; the generator's window is {config.NUM_CTX} tokens.")
    questions = select_questions(args, load_questions(PLANT_HOLDOUT))
    if args.inspect:
        context = stuffed_context(sections)
        ui.show_note(f"--mode stuff would fit {len(context.chunks)} of {len(sections)} sections.")
        return
    try:
        chunks = chunk_all(sections, config.SIZE, config.OVERLAP)
        index = Index.build(chunks, OllamaEmbedder(args.embed_model, cache=EmbeddingCache()))  # warms the cache for the server
        # --retriever compares another retriever in pipeline mode; it does not change config.py.
        retriever = args.retriever if "--retriever" in sys.argv else config.RETRIEVER
        search = {"semantic": index.search, "keyword": BM25(chunks).search,
                  "hybrid": HybridSearch(index, BM25(chunks)).search}[retriever]
        runs = []
        for number, question in enumerate(questions, start=1):
            ui.show_question(number, len(questions), question.text)
            row = run_one(args.mode, question, args, sections, chunks, search)
            if row["thinking"]:
                ui.show_note("Thinking · GENERATIVE MODEL (--think):\n" + row["thinking"])
            ui.show_table(f"{args.mode}", ["answer", "evidence", "facts", "citations", "note"],
                          [(row["answer"][:200], row["evidence"], row["facts"], row["citations"], row["note"])])
            runs.append(row)
    except OllamaError as exc:
        ui.show_error(str(exc))
        raise SystemExit(1) from None
    if args.eval:
        RESULTS.mkdir(parents=True, exist_ok=True)
        label = args.mode if args.mode != "pipeline" or retriever == config.RETRIEVER else f"pipeline-{retriever}"
        (RESULTS / f"exe09-{label}.json").write_text(json.dumps(runs, indent=1, ensure_ascii=False))
        compare()


if __name__ == "__main__":
    main()
