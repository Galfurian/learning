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
