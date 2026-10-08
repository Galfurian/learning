"""Copied from unit 03 (03-rag/src/raglab/evalset.py), trimmed to what unit 04 uses.

Retrieval is measured before any answer is generated: if the right section
is not retrieved, no prompt can fix the answer.
"""

import json
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .corpus import DEV_QUESTIONS
from .index import Hit



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
    # Section level (unit 03). Unit 04 metrics use metrics.first_evidence_rank.
    for position, hit in enumerate(hits, start=1):
        if hit.chunk.section_id in relevant:
            return position
    return None
