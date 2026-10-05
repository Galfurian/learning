"""The eval set and the retrieval metrics.

Retrieval is measured before any answer is generated: if the right section
is not retrieved, no prompt can fix the answer.
"""

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path

from .corpus import DEV_QUESTIONS
from .index import Hit

Results = dict[str, list[Hit]]


@dataclass(frozen=True)
class Question:
    id: str
    text: str
    relevant: frozenset[str]
    category: str
    answer: str
    must_contain: tuple[str, ...]

    @property
    def answerable(self) -> bool:
        return bool(self.relevant)


def load_questions(path: Path = DEV_QUESTIONS) -> list[Question]:
    rows = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        Question(r["id"], r["question"], frozenset(r["relevant"]), r["category"], r["answer"], tuple(r["must_contain"]))
        for r in rows
    ]


def first_relevant_rank(hits: Sequence[Hit], relevant: frozenset[str]) -> int | None:
    for position, hit in enumerate(hits, start=1):
        if hit.chunk.section_id in relevant:
            return position
    return None


def has_evidence(hits: Sequence[Hit], question: Question) -> bool:
    """Do these chunks contain what a correct answer needs?"""
    if not question.must_contain:
        return first_relevant_rank(hits, question.relevant) is not None
    text = " ".join(h.chunk.text for h in hits).lower()
    return all(needle.lower() in text for needle in question.must_contain)


def _answerable(questions: Sequence[Question]) -> list[Question]:
    found = [q for q in questions if q.answerable]
    if not found:
        raise ValueError("no answerable questions: the metric is undefined")
    return found


def recall_at_k(questions: Sequence[Question], results: Results, k: int) -> float:
    found = _answerable(questions)
    hits = sum((rank := first_relevant_rank(results[q.id], q.relevant)) is not None and rank <= k for q in found)
    return hits / len(found)


def evidence_at_k(questions: Sequence[Question], results: Results, k: int) -> float:
    found = _answerable(questions)
    return sum(has_evidence(results[q.id][:k], q) for q in found) / len(found)


def mrr(questions: Sequence[Question], results: Results) -> float:
    found = _answerable(questions)
    total = 0.0
    for q in found:
        rank = first_relevant_rank(results[q.id], q.relevant)
        total += 1 / rank if rank else 0.0
    return total / len(found)


def by_category(questions: Sequence[Question], results: Results, k: int) -> dict[str, tuple[int, int]]:
    table: dict[str, tuple[int, int]] = {}
    for q in _answerable(questions):
        rank = first_relevant_rank(results[q.id], q.relevant)
        hit, total = table.get(q.category, (0, 0))
        table[q.category] = (hit + (rank is not None and rank <= k), total + 1)
    return table


def run_search(questions: Sequence[Question], search: Callable[[str, int], list[Hit]], k: int) -> Results:
    return {q.id: search(q.text, k) for q in questions}
