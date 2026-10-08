"""Metrics with fixed names.

section_recall@k   a chunk of the right section is in the top k (R@k of unit 03)
evidence_recall@k  an evidence chunk (gain 2: right section and every fact) is in the top k
MRR                1 / rank of the first evidence chunk
nDCG@k             how well the top k is ordered, with gains 2 / 1 / 0

A reranker can only reorder the candidates the first stage found: for presence
metrics (the two recalls), the first stage's value at depth N is the most a
reranker can reach. MRR and nDCG can still change at equal recall.
"""

import math
from collections.abc import Sequence

from .corpus import Chunk
from .evalset import Question
from .generation import is_refusal
from .index import Hit

Results = dict[str, list[Hit]]


def gain(chunk: Chunk, question: Question) -> int:
    if chunk.section_id not in question.relevant:
        return 0
    text = chunk.text.lower()
    return 2 if all(m.lower() in text for m in question.must_contain) else 1


def ideal_gains(question: Question, chunks: Sequence[Chunk]) -> list[int]:
    return sorted((g for g in (gain(c, question) for c in chunks) if g > 0), reverse=True)


def first_evidence_rank(hits: Sequence[Hit], question: Question) -> int | None:
    for position, hit in enumerate(hits, start=1):
        if gain(hit.chunk, question) == 2:
            return position
    return None


def dcg(gains: Sequence[int], k: int) -> float:
    return sum((2**g - 1) / math.log2(i + 1) for i, g in enumerate(gains[:k], start=1))


def ndcg(hits: Sequence[Hit], question: Question, ideal: Sequence[int], k: int) -> float:
    best = dcg(ideal, k)
    if best == 0:
        return 0.0
    return dcg([gain(h.chunk, question) for h in hits], k) / best


def answerable(questions: Sequence[Question]) -> list[Question]:
    found = [q for q in questions if q.answerable]
    if not found:
        raise ValueError("no answerable questions: the metric is undefined")
    return found


def section_recall_at_k(questions: Sequence[Question], results: Results, k: int) -> float:
    found = answerable(questions)
    return sum(any(h.chunk.section_id in q.relevant for h in results[q.id][:k]) for q in found) / len(found)


def evidence_recall_at_k(questions: Sequence[Question], results: Results, k: int) -> float:
    found = answerable(questions)
    return sum((r := first_evidence_rank(results[q.id], q)) is not None and r <= k for q in found) / len(found)


def mrr(questions: Sequence[Question], results: Results) -> float:
    found = answerable(questions)
    return sum(1 / r if (r := first_evidence_rank(results[q.id], q)) else 0.0 for q in found) / len(found)


def mean_ndcg(questions: Sequence[Question], results: Results, ideals: dict[str, list[int]], k: int) -> float:
    found = answerable(questions)
    return sum(ndcg(results[q.id], q, ideals[q.id], k) for q in found) / len(found)


def _no_answer(questions: Sequence[Question]) -> list[Question]:
    found = [q for q in questions if not q.answerable]
    if not found:
        raise ValueError("no no-answer questions: the metric is undefined")
    return found


def false_answer_rate(questions: Sequence[Question], answers: dict[str, str]) -> float:
    found = _no_answer(questions)
    return sum(not is_refusal(answers[q.id]) for q in found) / len(found)


def abstention_accuracy(questions: Sequence[Question], answers: dict[str, str]) -> float:
    return 1.0 - false_answer_rate(questions, answers)


def metric_row(questions: Sequence[Question], results: Results, ideals: dict[str, list[int]]) -> dict[str, float]:
    return {
        "section_recall@3": section_recall_at_k(questions, results, 3),
        "evidence_recall@1": evidence_recall_at_k(questions, results, 1),
        "evidence_recall@3": evidence_recall_at_k(questions, results, 3),
        "MRR": mrr(questions, results),
        "nDCG@3": mean_ndcg(questions, results, ideals, 3),
    }
