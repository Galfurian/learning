import numpy as np
import pytest

from raglab.corpus import Chunk
from raglab.embedders import FakeEmbedder
from raglab.evalset import (
    Question,
    by_category,
    evidence_at_k,
    first_relevant_rank,
    has_evidence,
    load_questions,
    mrr,
    recall_at_k,
    run_search,
)
from raglab.index import Hit, Index


def chunk(cid, text):
    return Chunk(f"{cid}-1", cid, "Demo", cid, text)


CHUNKS = [
    chunk("belt", "belt tension squeal deflect"),
    chunk("oven", "lead-free profile peak 245"),
    chunk("lens", "clean focus lens alcohol"),
]


def test_search_ranks_by_cosine():
    index = Index.build(CHUNKS, FakeEmbedder(dim=256))
    hits = index.search("belt squeal", k=2)
    assert hits[0].chunk.section_id == "belt"
    assert hits[0].rank == 1 and hits[0].score > hits[1].score
    assert len(index.search("belt", k=10)) == 3


def test_zero_query_gives_zero_scores_not_nan():
    hits = Index.build(CHUNKS, FakeEmbedder(dim=256)).search("what is it?", k=3)
    assert [h.score for h in hits] == [0.0, 0.0, 0.0]


def test_index_rejects_vectors_that_are_not_unit_length():
    class Raw:
        name = "raw"

        def embed_documents(self, texts, titles=None):
            return np.full((len(texts), 4), 2.0, dtype=np.float32)

    with pytest.raises(ValueError, match="not unit length"):
        Index.build(CHUNKS, Raw())


def test_k_must_be_positive():
    with pytest.raises(ValueError):
        Index.build(CHUNKS, FakeEmbedder()).search("belt", k=0)


def q(qid, relevant, must=()):
    return Question(qid, "x", frozenset(relevant), "c", "", tuple(must))


def hits_for(*section_ids):
    return [Hit(chunk(s, f"text of {s}"), 1.0 - i / 10, i + 1) for i, s in enumerate(section_ids)]


def test_metrics():
    questions = [q("a", {"belt"}, ["text of belt"]), q("b", {"oven"}), q("c", set())]
    results = {"a": hits_for("belt", "oven"), "b": hits_for("lens", "oven"), "c": hits_for("lens")}
    assert first_relevant_rank(results["b"], frozenset({"oven"})) == 2
    assert recall_at_k(questions, results, 1) == 0.5
    assert recall_at_k(questions, results, 2) == 1.0
    assert mrr(questions, results) == pytest.approx((1 + 0.5) / 2)
    assert by_category(questions, results, 1) == {"c": (1, 2)}
    assert has_evidence(results["a"][:1], questions[0])
    # "b" has no must_contain: evidence means a relevant hit within k, and oven is rank 2.
    assert evidence_at_k(questions, results, 1) == 0.5


def test_metrics_need_answerable_questions():
    with pytest.raises(ValueError):
        recall_at_k([q("c", set())], {"c": []}, 3)


def test_run_search_and_load_questions():
    questions = load_questions()
    assert len(questions) == 26 and sum(not x.answerable for x in questions) == 4
    results = run_search(questions[:2], lambda text, k: hits_for("lens")[:k], 1)
    assert set(results) == {"d01", "d02"}
