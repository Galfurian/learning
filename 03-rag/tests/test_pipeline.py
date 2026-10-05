from raglab import pipeline
from raglab.client import ChatResult
from raglab.context import build_context, estimate_tokens, format_chunk
from raglab.corpus import Chunk
from raglab.generation import (
    REFUSAL,
    build_messages,
    check_citations,
    cited_ids,
)
from raglab.index import Hit


def chunk(cid, text="x" * 40):
    return Chunk(cid, cid.rsplit("-", 1)[0], "Demo", "T", text)


def hits(*ids, scores=None):
    scores = scores or [0.9 - i * 0.1 for i in range(len(ids))]
    return [Hit(chunk(i), s, r) for r, (i, s) in enumerate(zip(ids, scores), start=1)]


def test_build_context_order_dedupe_budget():
    found = hits("a-1", "b-1", "a-1", "c-1")
    # Each chunk costs its estimate + 1 (the blank line between chunks).
    budget = (estimate_tokens(format_chunk(chunk("a-1"))) + 1) * 2
    context = build_context(found, budget=budget)
    assert context.ids == ["a-1", "b-1"]
    assert [c.id for c in context.dropped] == ["c-1"]
    assert context.text.startswith("[a-1]\n")
    assert context.tokens <= budget


def test_budget_smaller_than_first_chunk_skips_it_but_tries_the_rest():
    big = Hit(chunk("a-1", "x" * 4000), 0.9, 1)
    small = Hit(chunk("b-1", "short"), 0.8, 2)
    context = build_context([big, small], budget=50)
    assert context.ids == ["b-1"] and [c.id for c in context.dropped] == ["a-1"]
    assert build_context([big], budget=50).chunks == []


def test_cited_ids_formats():
    assert cited_ids("A [lx40-cooling-1]. B [lx40-cooling-1, p3-temps-2] and [ p3-bed-1 ;rf9-x-3]") == [
        "lx40-cooling-1", "p3-temps-2", "p3-bed-1", "rf9-x-3",
    ]
    assert cited_ids("see [1] or [note]") == []


def test_check_citations():
    ids = ["a-1", "b-1"]
    assert check_citations("Yes. [a-1]", ids).ok
    report = check_citations("Yes. [z-9]", ids)
    assert not report.ok and report.unknown == ["z-9"]
    assert check_citations("Yes.", ids).problem == "no citations"
    refused = check_citations("Not in the manuals.", ids)
    assert refused.ok and refused.refused
    assert not check_citations("Not in the manuals. [a-1]", ids).ok


def test_messages_contain_context_and_question():
    context = build_context(hits("a-1"), 1500)
    messages = build_messages("Why?", context)
    assert messages[0]["role"] == "system" and "[" in messages[0]["content"]
    assert "[a-1]" in messages[1]["content"] and messages[1]["content"].endswith("Question: Why?")


def fake_chat(content):
    def chat(model, messages, **kwargs):
        return ChatResult(content, "", [], {"content": content}, 100, 5, 0.1, {})
    return chat


def test_answer_question_calls_generator(monkeypatch):
    monkeypatch.setattr(pipeline, "chat", fake_chat("It is 22 °C. [a-1]"))
    trace = pipeline.answer_question("q", lambda text, k: hits("a-1", "b-1")[:k], k=2)
    assert trace.answer == "It is 22 °C. [a-1]" and trace.citations.ok and not trace.abstained


def test_answer_question_abstains_on_threshold_without_calling_generator(monkeypatch):
    monkeypatch.setattr(pipeline, "chat", lambda *a, **k: (_ for _ in ()).throw(AssertionError("called")))
    trace = pipeline.answer_question("q", lambda text, k: hits("a-1", scores=[0.2]), min_score=0.5)
    assert trace.abstained and trace.abstain_reason == "threshold" and trace.answer == REFUSAL


def test_answer_question_abstains_on_budget(monkeypatch):
    monkeypatch.setattr(pipeline, "chat", lambda *a, **k: (_ for _ in ()).throw(AssertionError("called")))
    big = [Hit(chunk("a-1", "x" * 4000), 0.9, 1)]
    trace = pipeline.answer_question("q", lambda text, k: big, budget=50)
    assert trace.abstained and trace.abstain_reason == "budget"


def test_trace_record_is_json_ready(monkeypatch):
    import json

    monkeypatch.setattr(pipeline, "chat", fake_chat("x [a-1]"))
    trace = pipeline.answer_question("q", lambda text, k: hits("a-1"))
    record = pipeline.trace_record(trace, None, {"k": 3})
    json.dumps(record)
    assert record["context"] == [{"id": "a-1", "section_id": "a"}]
    assert record["labels"] == {"answer_correct": None, "supported": None}

