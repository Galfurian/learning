from types import SimpleNamespace

from raglab.agent import excerpts_from, to_ollama_tool


def test_to_ollama_tool():
    tool = SimpleNamespace(name="search_manuals", description="Search.", input_schema={"type": "object"})
    assert to_ollama_tool(tool) == {
        "type": "function",
        "function": {"name": "search_manuals", "description": "Search.", "parameters": {"type": "object"}},
    }


def test_excerpts_from_structured_and_text():
    found = [{"id": "a-1", "section_id": "a", "text": "x"}]
    assert excerpts_from({"excerpts": found}) == found
    assert excerpts_from({"result": {"excerpts": found}}) == found
    assert excerpts_from([{"type": "text", "text": '{"excerpts": [{"id": "a-1", "section_id": "a", "text": "x"}]}'}]) == found
    assert excerpts_from({"unexpected": 1}) == []


def test_ollama_error_in_tool_mode_is_not_hidden_in_an_exception_group(monkeypatch):
    import asyncio
    from pathlib import Path

    import pytest

    from raglab import agent
    from raglab.client import OllamaError

    def fail(*args, **kwargs):
        raise OllamaError('model "nope" not found, try pulling it first. Run: ollama pull nope')

    monkeypatch.setattr(agent, "chat", fail)
    server = Path(__file__).resolve().parents[1] / "exercises" / "exe09-demo" / "manual_server.py"
    with pytest.raises(OllamaError, match="ollama pull nope"):
        asyncio.run(agent.run_tool_agent("q", server, model="nope", num_ctx=2048))


def test_tool_agent_passes_think_and_keeps_the_thinking(monkeypatch):
    import asyncio
    from pathlib import Path

    from raglab import agent
    from raglab.client import ChatResult

    seen = {}

    def chat(model, messages, **kwargs):
        seen.update(kwargs)
        return ChatResult("Not in the manuals.", "No search needed.", [], {"role": "assistant"}, 10, 2, 0.1, {})

    monkeypatch.setattr(agent, "chat", chat)
    server = Path(__file__).resolve().parents[1] / "exercises" / "exe09-demo" / "manual_server.py"
    run = asyncio.run(agent.run_tool_agent("q", server, model="m", num_ctx=2048, think=True))
    assert seen["think"] is True
    assert run.thinking == "No search needed."
