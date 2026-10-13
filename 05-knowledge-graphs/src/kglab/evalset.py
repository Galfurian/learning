"""The questions of the line, with their gold path and gold answers."""

import json
from dataclasses import dataclass, field
from pathlib import Path

TYPES = ("single", "multi-hop", "aggregation", "alias", "no-answer")


@dataclass(frozen=True)
class GoldPath:
    start: tuple[str, ...]
    relations: tuple[str, ...]


@dataclass(frozen=True)
class Question:
    id: str
    question: str
    type: str
    gold_path: GoldPath | None
    gold_answers: tuple[str, ...]
    count: int | None = None
    relevant: tuple[str, ...] = ()
    abstain_subtype: str | None = None
    ambiguous: tuple[str, ...] = field(default=())

    @property
    def answerable(self) -> bool:
        return self.type != "no-answer" and not self.ambiguous


def parse_question(item: dict) -> Question:
    if item["type"] not in TYPES:
        raise ValueError(f"{item.get('id')}: type {item['type']!r} is not one of {TYPES}")
    path = item.get("gold_path")
    return Question(
        id=item["id"],
        question=item["question"],
        type=item["type"],
        gold_path=GoldPath(tuple(path["start"]), tuple(path["relations"])) if path else None,
        gold_answers=tuple(item.get("gold_answers", [])),
        count=item.get("count"),
        relevant=tuple(item.get("relevant", [])),
        abstain_subtype=item.get("abstain_subtype"),
        ambiguous=tuple(item.get("ambiguous", [])),
    )


def load_questions(path: Path) -> list[Question]:
    questions = [parse_question(item) for item in json.loads(Path(path).read_text(encoding="utf-8"))]
    ids = [q.id for q in questions]
    if len(set(ids)) != len(ids):
        raise ValueError(f"{path}: duplicate question ids")
    return questions
