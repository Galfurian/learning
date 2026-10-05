"""One question through the whole pipeline: retrieve, build context, generate, check.

If nothing survives the threshold or the budget, the APP abstains and the
generator is never called.
"""

import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from .client import DEFAULT_CHAT_MODEL, Tracer, chat
from .context import DEFAULT_BUDGET, Context, build_context
from .evalset import Question
from .generation import (
    REFUSAL,
    SYSTEM_PROMPT,
    CitationReport,
    build_messages,
    check_citations,
)
from .index import Hit

Search = Callable[[str, int], list[Hit]]
ContextBuilder = Callable[[Sequence[Hit], int], Context]


@dataclass
class Trace:
    question: str
    k: int
    hits: list[Hit]
    kept: list[Hit]
    context: Context
    messages: list[dict]
    answer: str
    citations: CitationReport
    abstained: bool
    abstain_reason: str
    model: str
    prompt_tokens: int
    seconds_retrieval: float
    seconds_generation: float
    thinking: str = ""


def answer_question(
    question: str,
    search: Search,
    *,
    k: int = 3,
    budget: int = DEFAULT_BUDGET,
    min_score: float | None = None,
    model: str = DEFAULT_CHAT_MODEL,
    think: bool = False,
    num_ctx: int | None = None,
    system_prompt: str = SYSTEM_PROMPT,
    context_builder: ContextBuilder = build_context,
    tracer: Tracer | None = None,
) -> Trace:
    started = time.perf_counter()
    hits = search(question, k)
    seconds_retrieval = time.perf_counter() - started
    kept = [h for h in hits if min_score is None or h.score >= min_score]
    context = context_builder(kept, budget)
    messages = build_messages(question, context, system_prompt)

    reason = ""
    if not hits:
        reason = "no hits"
    elif not kept:
        reason = "threshold"
    elif not context.chunks:
        reason = "budget"
    if reason:
        return Trace(question, k, hits, kept, context, messages, REFUSAL,
                     check_citations(REFUSAL, []), True, reason, model, 0, seconds_retrieval, 0.0)

    result = chat(model, messages, think=think, num_ctx=num_ctx, tracer=tracer)
    return Trace(question, k, hits, kept, context, messages, result.content,
                 check_citations(result.content, context.ids), False, "", model,
                 result.prompt_tokens, seconds_retrieval, result.seconds, result.thinking)


def trace_record(trace: Trace, question: Question | None, settings: dict[str, Any]) -> dict[str, Any]:
    """A trace as plain JSON, for EXE08. A person fills in the labels."""
    return {
        "question": trace.question,
        "relevant": sorted(question.relevant) if question else [],
        "answerable": question.answerable if question else None,
        "settings": settings,
        "hits": [
            {"id": h.chunk.id, "section_id": h.chunk.section_id, "score": round(h.score, 4), "rank": h.rank}
            for h in trace.hits
        ],
        "context": [{"id": c.id, "section_id": c.section_id} for c in trace.context.chunks],
        "answer": trace.answer,
        "abstained": trace.abstained,
        "abstain_reason": trace.abstain_reason,
        "labels": {"answer_correct": None, "supported": None},
    }
