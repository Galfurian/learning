import json

import pytest

from reranklab import client
from reranklab.chunking import chunk_all
from reranklab.corpus import DEV_QUESTIONS, PLANT_MANUALS, load_manuals
from reranklab.generation import REFUSAL, answer_ok, check_citations, is_refusal
from reranklab.evalset import load_questions
from reranklab.index import Hit


@pytest.mark.parametrize(
    "value, url",
    [
        ("", "http://127.0.0.1:11434"),
        ("192.0.2.10:11434", "http://192.0.2.10:11434"),
        ("http://lab:11434/", "http://lab:11434"),
        ("http://lab", "http://lab:11434"),
    ],
)
def test_ollama_url_follows_ollama_host(monkeypatch, value, url):
    monkeypatch.setenv("OLLAMA_HOST", value)
    assert client.ollama_url() == url


def test_decide_posts_to_systemone(monkeypatch):
    sent = {}

    def fake_post(url, body, timeout=600):
        sent["url"], sent["body"] = url, body
        return {"answers": {"relevant": {"type": "noul", "noul": 0.9}}}

    monkeypatch.delenv("OLLAMA_HOST", raising=False)
    monkeypatch.setattr(client, "post", fake_post)
    result = client.decide("tev1:4b-q4_K_M", "state", {"relevant": {"type": "noul", "instructions": "?"}})
    assert sent["url"] == "http://127.0.0.1:11434/v1/systemone"
    assert result.answers["relevant"]["noul"] == 0.9


def test_hit_keeps_first_rank_fields():
    hit = Hit(chunk=None, score=0.5, rank=1)
    assert hit.first_rank is None and hit.rerank_score is None


def test_refusal_helpers():
    assert is_refusal("Not in the manuals.") and not is_refusal("32 m/min. [a-1]")
    assert check_citations(REFUSAL, ["a-1"]).ok


def test_dev_set_labels_point_at_real_facts():
    sections = load_manuals(PLANT_MANUALS)
    ids = {s.id for s in sections}
    questions = load_questions(DEV_QUESTIONS)
    assert len(questions) == 37 and sum(not q.answerable for q in questions) == 4
    for q in questions:
        assert set(q.relevant) <= ids, q.id
        text = " ".join(s.text for s in sections if s.id in q.relevant).lower()
        assert all(m.lower() in text for m in q.must_contain), q.id
    assert len(chunk_all(sections)) == 600


def test_holdout_is_fresh_and_labeled():
    from reranklab.corpus import HOLDOUT_QUESTIONS

    sections = load_manuals(PLANT_MANUALS)
    holdout = load_questions(HOLDOUT_QUESTIONS)
    dev_machines = {s.split("-")[0] for q in load_questions(DEV_QUESTIONS) for s in q.relevant}
    assert len(holdout) == 20 and sum(not q.answerable for q in holdout) == 3
    for q in holdout:
        assert not {s.split("-")[0] for s in q.relevant} & dev_machines, q.id
        text = " ".join(s.text for s in sections if s.id in q.relevant).lower()
        assert all(m.lower() in text for m in q.must_contain), q.id


def test_read_timeout_is_one_clear_error(monkeypatch):
    def slow(request, timeout):
        raise TimeoutError("timed out")

    monkeypatch.setattr(client, "urlopen", slow)
    with pytest.raises(client.OllamaError, match="did not answer within"):
        client.post("http://lab:11434/v1/systemone", {})
