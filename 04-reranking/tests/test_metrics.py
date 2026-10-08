import math

import pytest

from reranklab.corpus import Chunk
from reranklab.evalset import Question
from reranklab.index import Hit
from reranklab.metrics import (
    abstention_accuracy, dcg, evidence_recall_at_k, false_answer_rate, first_evidence_rank, gain,
    ideal_gains, metric_row, mean_ndcg, mrr, ndcg, section_recall_at_k,
)


def chunk(cid, text):
    return Chunk(cid, cid.rsplit("-", 1)[0], "M", "T", text)


Q = Question("q1", "x", frozenset({"m-errors"}), "code", "", ("E-1",))
NONE = Question("n1", "x", frozenset(), "no-answer", "", ())
EVIDENCE = chunk("m-errors-2", "E-1: fan stopped")
SAME_SECTION = chunk("m-errors-1", "E-2: door open")
OTHER = chunk("m-parts-1", "PN-1: lens")


def hits(*chunks):
    return [Hit(c, 1.0 - i / 10, i + 1) for i, c in enumerate(chunks)]


def test_gain():
    assert (gain(EVIDENCE, Q), gain(SAME_SECTION, Q), gain(OTHER, Q)) == (2, 1, 0)


def test_ideal_gains_and_first_evidence_rank():
    assert ideal_gains(Q, [OTHER, SAME_SECTION, EVIDENCE]) == [2, 1]
    assert first_evidence_rank(hits(SAME_SECTION, EVIDENCE), Q) == 2
    assert first_evidence_rank(hits(OTHER), Q) is None


def test_dcg_and_ndcg():
    assert dcg([2, 1], 2) == pytest.approx(3 + 1 / math.log2(3))
    ideal = [2, 1]
    assert ndcg(hits(EVIDENCE, SAME_SECTION), Q, ideal, 2) == pytest.approx(1.0)
    swapped = ndcg(hits(SAME_SECTION, EVIDENCE), Q, ideal, 2)
    assert 0 < swapped < 1
    assert ndcg(hits(OTHER), Q, [], 3) == 0.0


def test_reorder_changes_ndcg_but_not_recall():
    a = {"q1": hits(SAME_SECTION, OTHER, EVIDENCE)}
    b = {"q1": hits(EVIDENCE, SAME_SECTION, OTHER)}
    ideals = {"q1": [2, 1]}
    assert section_recall_at_k([Q], a, 3) == section_recall_at_k([Q], b, 3) == 1.0
    assert evidence_recall_at_k([Q], a, 3) == evidence_recall_at_k([Q], b, 3) == 1.0
    assert mean_ndcg([Q], a, ideals, 3) < mean_ndcg([Q], b, ideals, 3)
    assert evidence_recall_at_k([Q], a, 1) == 0.0 and evidence_recall_at_k([Q], b, 1) == 1.0
    assert mrr([Q], a) == pytest.approx(1 / 3)


def test_no_answer_questions_are_skipped_by_retrieval_metrics():
    results = {"q1": hits(EVIDENCE), "n1": hits(OTHER)}
    assert evidence_recall_at_k([Q, NONE], results, 1) == 1.0
    with pytest.raises(ValueError):
        mrr([NONE], results)


def test_false_answer_rate():
    answers = {"q1": "x", "n1": "Two years. [m-parts-1]", "n2": "Not in the manuals."}
    n2 = Question("n2", "x", frozenset(), "no-answer", "", ())
    assert false_answer_rate([Q, NONE, n2], answers) == 0.5
    assert abstention_accuracy([Q, NONE, n2], answers) == 0.5
    with pytest.raises(ValueError):
        false_answer_rate([Q], answers)


def test_metric_row_keys():
    row = metric_row([Q], {"q1": hits(EVIDENCE)}, {"q1": [2, 1]})
    assert set(row) == {"section_recall@3", "evidence_recall@1", "evidence_recall@3", "MRR", "nDCG@3"}
