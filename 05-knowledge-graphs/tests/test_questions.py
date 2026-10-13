import json
from pathlib import Path

from kglab.corpus import load_notes
from kglab.evalset import load_questions
from kglab.graph import follow, load
from kglab.parse import model_chunks


ROOT = Path(__file__).parents[1]
DATA = ROOT / "data"


def question_sets() -> list[tuple[Path, list]]:
    paths = [DATA / "dev.json"]
    holdout = DATA / "holdout.json"
    if holdout.exists():
        paths.append(holdout)
    return [(path, load_questions(path)) for path in paths]


def test_question_ids_are_unique_across_splits():
    questions = [question for _, items in question_sets() for question in items]
    ids = [question.id for question in questions]
    assert len(ids) == len(set(ids))


def test_gold_paths_follow_to_gold_answers():
    graph = load(DATA / "gold.json")
    for path, questions in question_sets():
        for question in questions:
            if question.gold_path is None:
                assert question.gold_answers == (), path / question.id
                continue
            answers = follow(graph, question.gold_path.start, question.gold_path.relations)
            assert answers == list(question.gold_answers), path / question.id
            if question.count is not None:
                assert question.count == len(answers), path / question.id


def test_relevant_ids_are_real_note_or_model_chunks():
    note_ids = {chunk.id for chunk in load_notes(DATA / "line" / "notes")}
    model_ids = {chunk.id for chunk in model_chunks(DATA / "line" / "models")}
    valid = note_ids | model_ids
    for path, questions in question_sets():
        for question in questions:
            assert set(question.relevant) <= valid, path / question.id


def test_dev_covers_required_question_shapes():
    questions = load_questions(DATA / "dev.json")
    assert len(questions) >= 40
    assert any(q.type == "single" and q.gold_path and len(q.gold_path.relations) == 1 for q in questions)
    assert any(q.type == "multi-hop" and q.gold_path and len(q.gold_path.relations) >= 3 for q in questions)
    assert any(q.count is not None for q in questions)
    assert sum(q.type == "alias" for q in questions) >= 3
    assert sum(q.type == "no-answer" for q in questions) >= 4


def test_no_answer_and_ambiguous_questions_are_explicit():
    questions = [question for _, items in question_sets() for question in items]
    for question in questions:
        if question.type == "no-answer":
            assert question.gold_path is None
            assert question.abstain_subtype
        if question.ambiguous:
            assert question.gold_path is None
            assert question.gold_answers == ()


def test_question_files_are_json_arrays():
    for path, _ in question_sets():
        value = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(value, list)
