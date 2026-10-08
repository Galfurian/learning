"""One question through first stage -> reranker -> generator, and the first failing stage."""

import time
from dataclasses import dataclass

from .client import Tracer, chat
from .evalset import Question
from .generation import CitationReport, Context, answer_ok, build_context, build_messages, check_citations, is_refusal
from .index import Hit
from .metrics import gain
from .rerankers import Reranker, rerank
from .retriever import FirstStage


def hit_record(hit: Hit, question: Question) -> dict:
    return {"id": hit.chunk.id, "section_id": hit.chunk.section_id, "gain": gain(hit.chunk, question),
            "first_rank": hit.first_rank, "rank": hit.rank, "score": round(hit.score, 4),
            "rerank_score": None if hit.rerank_score is None else round(hit.rerank_score, 4)}


@dataclass
class Run:
    question: Question
    candidates: list[Hit]
    top: list[Hit]
    context: Context
    messages: list[dict]
    answer: str
    thinking: str
    citations: CitationReport
    seconds: dict[str, float]
    rerank_requests: int


def run_question(question: Question, first_stage: FirstStage, reranker: Reranker | None, *, depth: int, k: int,
                 model: str, think: bool = False, generate: bool = True, tracer: Tracer | None = None) -> Run:
    seconds = {"first_stage": 0.0, "rerank": 0.0, "generation": 0.0}
    started = time.perf_counter()
    candidates = first_stage.candidates(question.text, depth)
    seconds["first_stage"] = time.perf_counter() - started
    requests_before = getattr(reranker, "requests", 0)
    started = time.perf_counter()
    top = rerank(question.text, candidates, reranker, k) if reranker else candidates[:k]
    seconds["rerank"] = time.perf_counter() - started
    requests = getattr(reranker, "requests", 0) - requests_before
    context = build_context(top)
    messages = build_messages(question.text, context)
    answer, thinking = "", ""
    if generate:
        result = chat(model, messages, think=think, tracer=tracer)
        answer, thinking, seconds["generation"] = result.content, result.thinking, result.seconds
    return Run(question, candidates, top, context, messages, answer, thinking,
               check_citations(answer, context.ids), seconds, requests)


def row(run: Run) -> dict:
    q = run.question
    return {
        "question_id": q.id, "category": q.category, "answerable": q.answerable,
        "candidates": [hit_record(h, q) for h in run.candidates], "top": [hit_record(h, q) for h in run.top],
        "answer": run.answer, "facts": answer_ok(run.answer, q), "citations_ok": run.citations.ok,
        "refused": is_refusal(run.answer), "seconds": {k: round(v, 3) for k, v in run.seconds.items()},
        "rerank_requests": run.rerank_requests,
    }


def diagnose(record: dict) -> str:
    """The first stage that failed, in a fixed order. Operational, not causal."""
    if not record["answerable"]:
        return "NONE" if record["refused"] else "GENERATION"
    if not any(c["gain"] == 2 for c in record["candidates"]):
        return "CANDIDATES"
    if not any(c["gain"] == 2 for c in record["top"]):
        return "RERANK"
    if not (record["facts"] and record["citations_ok"]):
        return "GENERATION"
    return "NONE"
