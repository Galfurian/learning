from reranklab import costs


def test_timing_properties():
    t = costs.Timing("minilm", "CPU", pairs=20, questions=2, requests=0, seconds=0.6, load_seconds=0.4)
    assert t.ms_per_pair == 30.0 and t.s_per_question == 0.3


def test_is_local(monkeypatch):
    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    assert costs.is_local()
    monkeypatch.setenv("OLLAMA_HOST", "192.0.2.10:11434")
    assert not costs.is_local()


def test_save_and_load(tmp_path):
    t = costs.Timing("tev1-A", "CPU", 30, 3, 30, 90.0, 6.0)
    path = tmp_path / "t.json"
    costs.save_timing(t, path)
    assert costs.load_timing(path) == t and costs.load_timing(tmp_path / "missing.json") is None


def test_best_under_budget():
    rows = [
        {"config": "none", "evidence_recall@1": 0.6, "nDCG@3": 0.6, "s/question": 0.0},
        {"config": "minilm-20", "evidence_recall@1": 0.9, "nDCG@3": 0.8, "s/question": 0.7},
        {"config": "minilm-50", "evidence_recall@1": 0.9, "nDCG@3": 0.85, "s/question": 1.6},
        {"config": "tev1-20", "evidence_recall@1": 0.95, "nDCG@3": 0.9, "s/question": 40.0},
    ]
    assert costs.best_under_budget(rows, 1.0)["config"] == "minilm-20"
    assert costs.best_under_budget(rows, 2.0)["config"] == "minilm-50"
    assert costs.best_under_budget(rows, 100)["config"] == "tev1-20"
    assert costs.best_under_budget(rows, -1) is None
