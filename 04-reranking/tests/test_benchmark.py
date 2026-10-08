from reranklab import benchmark
from reranklab.client import ChatResult
from reranklab.corpus import Chunk
from reranklab.evalset import Question
from reranklab.index import Hit
from reranklab.rerankers import FakeReranker

Q = Question("q1", "Which fan stopped? E-1", frozenset({"m-errors"}), "code", "", ("E-1",))
NONE = Question("n1", "warranty?", frozenset(), "no-answer", "", ())
EVIDENCE = Chunk("m-errors-2", "m-errors", "M", "Error codes", "E-1: fan stopped")
OTHER = Chunk("m-parts-1", "m-parts", "M", "Spare parts", "PN-1: lens")


class Stage:
    name = "fixed"

    def __init__(self, chunks):
        self.chunks = chunks

    def candidates(self, question, depth):
        return [Hit(c, 0.5, i, first_rank=i) for i, c in enumerate(self.chunks[:depth], start=1)]


def fake_chat(content):
    return lambda model, messages, **kw: ChatResult(content, "", [], {}, 50, 3, 0.2, {})


def test_run_question_reranks_then_generates(monkeypatch):
    monkeypatch.setattr(benchmark, "chat", fake_chat("The fan. [m-errors-2]"))
    run = benchmark.run_question(Q, Stage([OTHER, EVIDENCE]), FakeReranker(), depth=2, k=1, model="m")
    assert [h.chunk.id for h in run.top] == ["m-errors-2"] and run.top[0].first_rank == 2
    row = benchmark.row(run)
    assert row["top"][0]["gain"] == 2 and row["citations_ok"] and row["facts"] is False


def test_without_reranker_top_k_is_the_first_stage_order(monkeypatch):
    monkeypatch.setattr(benchmark, "chat", fake_chat("Not in the manuals."))
    run = benchmark.run_question(Q, Stage([OTHER, EVIDENCE]), None, depth=2, k=1, model="m")
    assert [h.chunk.id for h in run.top] == ["m-parts-1"] and run.rerank_requests == 0


def test_generate_false_skips_the_generator(monkeypatch):
    monkeypatch.setattr(benchmark, "chat", lambda *a, **k: (_ for _ in ()).throw(AssertionError("called")))
    run = benchmark.run_question(Q, Stage([EVIDENCE]), None, depth=1, k=1, model="m", generate=False)
    assert run.answer == ""


def record(gains_candidates, gains_top, answerable=True, facts=True, citations=True, refused=False):
    return {"answerable": answerable, "facts": facts, "citations_ok": citations, "refused": refused,
            "candidates": [{"gain": g} for g in gains_candidates], "top": [{"gain": g} for g in gains_top]}


def test_diagnose_first_failing_stage():
    assert benchmark.diagnose(record([0, 1], [1])) == "CANDIDATES"
    assert benchmark.diagnose(record([0, 2], [0])) == "RERANK"
    assert benchmark.diagnose(record([2], [2], facts=False)) == "GENERATION"
    assert benchmark.diagnose(record([2], [2], citations=False)) == "GENERATION"
    assert benchmark.diagnose(record([2], [2])) == "NONE"
    assert benchmark.diagnose(record([0], [0], answerable=False, refused=True)) == "NONE"
    assert benchmark.diagnose(record([0], [0], answerable=False, refused=False)) == "GENERATION"
