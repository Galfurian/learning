import argparse

import pytest

from reranklab import costs, rerankers, runners
from reranklab.exercise import select_questions
from reranklab.evalset import Question
from reranklab.scorecache import ScoreCache


def test_tev1_fill_hint_uses_the_library_reranker_id():
    # EXE06 reads the cache with the library Tev1Reranker; the hint must name a command that writes those keys.
    assert "exe00-demo/exe00.py --reranker tev1-a --eval" in runners.TEV1_FILL_HINT
    assert rerankers.make_reranker("tev1-a", cache=False).id == rerankers.Tev1Reranker().id


def test_cross_encoder_cpu_cost_comes_from_a_measurement(tmp_path):
    t = costs.Timing("minilm-batch1", "CPU", pairs=100, questions=5, requests=0, seconds=2.0, load_seconds=0.1)
    costs.save_timing(t, tmp_path / "minilm-cpu.json")
    records = [{"candidates": [{}] * 20}, {"candidates": [{}] * 10}]
    assert costs.reranker_cpu_seconds("minilm", records, tmp_path) == pytest.approx(0.3)  # 20 ms/pair * 15
    assert costs.reranker_cpu_seconds("bge", records, tmp_path) is None
    assert costs.reranker_cpu_seconds("embedding", records, tmp_path) == 0.0


@pytest.mark.parametrize("extra", [{"case": 3}, {"question": "x"}])
def test_eval_refuses_a_partial_selection(extra):
    args = argparse.Namespace(eval=True, case=None, question=None) 
    for key, value in extra.items():
        setattr(args, key, value)
    with pytest.raises(SystemExit, match="--eval runs the whole set"):
        select_questions(args, [Question("q1", "x", frozenset({"a"}), "c", "", ())])


@pytest.mark.parametrize("host, local", [("", True), ("0.0.0.0", True), ("[::1]:11434", True),
                                          ("localhost:11434", True), ("192.0.2.10:11434", False)])
def test_is_local(monkeypatch, host, local):
    monkeypatch.setenv("OLLAMA_HOST", host)
    assert costs.is_local() is local


def test_mode_b_cache_key_includes_the_question_wording(monkeypatch, tmp_path):
    calls = []

    def fake_decide(model, state, questions, tracer=None):
        calls.append(1)
        return type("R", (), {"answers": {k: {"noul": 0.5} for k in questions}})()

    monkeypatch.setattr(rerankers, "decide", fake_decide)
    cache = ScoreCache(tmp_path)
    rerankers.Tev1Reranker(mode="B", cache=cache).score("q", ["a", "b"])
    original = rerankers.questions_b
    monkeypatch.setattr(rerankers, "questions_b",
                        lambda n: {k: {**v, "instructions": v["instructions"] + " Answer strictly."} for k, v in original(n).items()})
    rerankers.Tev1Reranker(mode="B", cache=cache).score("q", ["a", "b"])
    assert len(calls) == 2
