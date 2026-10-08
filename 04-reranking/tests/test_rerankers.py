import numpy as np
import pytest

from reranklab import rerankers
from reranklab.checks import fake_chunk
from reranklab.index import Hit
from reranklab.rerankers import (
    FakeReranker, Tev1Reranker, questions_b, rerank, state_a, state_b,
)
from reranklab.scorecache import ScoreCache


def hits(*texts):
    return [Hit(fake_chunk(f"c{i}-1", t), 0.5, i, first_rank=i) for i, t in enumerate(texts, start=1)]


class Fixed:
    id = "fixed"

    def __init__(self, scores):
        self.scores = scores

    def score(self, question, passages):
        return self.scores[: len(passages)]


def test_rerank_orders_cuts_and_keeps_first_rank():
    out = rerank("q", hits("a", "b", "c"), Fixed([0.1, 0.9, 0.5]), k=2)
    assert [h.chunk.id for h in out] == ["c2-1", "c3-1"]
    assert [h.rank for h in out] == [1, 2] and [h.first_rank for h in out] == [2, 3]
    assert out[0].rerank_score == 0.9 and out[0].kind == "rerank"


def test_rerank_is_stable_on_ties_and_handles_short_lists():
    out = rerank("q", hits("a", "b"), Fixed([0.5, 0.5]), k=10)
    assert [h.chunk.id for h in out] == ["c1-1", "c2-1"]
    assert rerank("q", [], Fixed([]), k=3) == []


def test_fake_reranker_is_deterministic():
    fake = FakeReranker()
    scores = fake.score("belt speed of the C-83", ["The belt speed is 32 m/min", "door seal"])
    assert scores[0] > scores[1] and scores == fake.score("belt speed of the C-83", ["The belt speed is 32 m/min", "door seal"])


def test_tev1_states():
    assert "Question: q" in state_a("q", "the passage") and "the passage" in state_a("q", "the passage")
    b = state_b("q", ["one", "two"])
    assert "Passage 1:\none" in b and "Passage 2:\ntwo" in b
    assert list(questions_b(2)) == ["p1", "p2"] and questions_b(2)["p2"]["type"] == "noul"


def test_tev1_mode_a_one_request_per_passage(monkeypatch):
    calls = []

    def fake_decide(model, state, questions, tracer=None):
        calls.append(state)
        p = 0.9 if "right" in state else 0.1
        return type("R", (), {"answers": {"relevant": {"noul": p}}})()

    monkeypatch.setattr(rerankers, "decide", fake_decide)
    reranker = Tev1Reranker(mode="A")
    assert reranker.score("q", ["wrong", "right"]) == [0.1, 0.9]
    assert len(calls) == 2 and reranker.requests == 2


def test_tev1_mode_b_reversed_order_maps_scores_back(monkeypatch):
    seen = {}

    def fake_decide(model, state, questions, tracer=None):
        seen["state"] = state
        # passage 1 in the prompt gets 0.8, passage 2 gets 0.2
        return type("R", (), {"answers": {"p1": {"noul": 0.8}, "p2": {"noul": 0.2}}})()

    monkeypatch.setattr(rerankers, "decide", fake_decide)
    scores = Tev1Reranker(mode="B", order="reversed").score("q", ["first", "second"])
    assert seen["state"].index("second") < seen["state"].index("first")
    assert scores == [0.2, 0.8]


def test_score_cache_keys_include_every_part(tmp_path):
    cache = ScoreCache(tmp_path)
    assert cache.key(["minilm@abc", "pair-v1", "", "q", "p"]) != cache.key(["minilm@abc", "pair-v2", "", "q", "p"])
    cache.put(["a", "q"], 1.5)
    assert cache.get(["a", "q"]) == 1.5 and cache.get(["b", "q"]) is None


def test_tev1_uses_the_cache(monkeypatch, tmp_path):
    calls = []

    def fake_decide(model, state, questions, tracer=None):
        calls.append(1)
        return type("R", (), {"answers": {"relevant": {"noul": 0.7}}})()

    monkeypatch.setattr(rerankers, "decide", fake_decide)
    reranker = Tev1Reranker(mode="A", cache=ScoreCache(tmp_path))
    reranker.score("q", ["p"])
    reranker.score("q", ["p"])
    assert len(calls) == 1


class FakeEncoding:
    ids, attention_mask, type_ids = [1, 2, 3], [1, 1, 1], [0, 0, 1]


class FakeTokenizer:
    def encode(self, a, b):
        return FakeEncoding()


class FakeInput:
    def __init__(self, name):
        self.name = name


class FakeSession:
    def get_inputs(self):
        return [FakeInput("input_ids"), FakeInput("attention_mask"), FakeInput("token_type_ids")]

    def run(self, outputs, feed):
        assert feed["input_ids"].dtype == np.int64 and feed["input_ids"].shape == (1, 3)
        return [np.array([[2.5]], dtype=np.float32)]


def test_cross_encoder_download_failure_is_one_clear_error(monkeypatch):
    import huggingface_hub

    def offline(*args, **kwargs):
        raise OSError("no network")

    monkeypatch.setattr(huggingface_hub, "hf_hub_download", offline)
    with pytest.raises(RuntimeError, match="Xenova/ms-marco-MiniLM-L-6-v2@a09144355ade"):
        rerankers.CrossEncoderReranker(rerankers.MINILM).score_pair("q", "p")


def test_cross_encoder_score_pair_with_fakes():
    reranker = rerankers.CrossEncoderReranker(rerankers.MINILM)
    reranker._tokenizer, reranker._session = FakeTokenizer(), FakeSession()
    value = reranker.score_pair("q", "p")
    assert value == pytest.approx(2.5) and isinstance(value, float)
