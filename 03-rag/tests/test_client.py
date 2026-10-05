import io
import json
from urllib.error import HTTPError, URLError

import pytest

from raglab import client


def test_embed_body_is_plain_json():
    assert client.embed_body("embeddinggemma", ["a", "b"]) == {
        "model": "embeddinggemma",
        "input": ["a", "b"],
    }


def test_chat_body_defaults_and_options():
    messages = [{"role": "user", "content": "hi"}]
    assert client.chat_body("qwen3:1.7b", messages) == {
        "model": "qwen3:1.7b",
        "messages": messages,
        "stream": False,
        "think": False,
    }
    body = client.chat_body("m", messages, think=True, num_ctx=8192, tools=[{"type": "function"}])
    assert body["think"] is True
    assert body["options"] == {"num_ctx": 8192}
    assert body["tools"] == [{"type": "function"}]


class FakeResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_post_returns_json(monkeypatch):
    monkeypatch.setattr(client, "urlopen", lambda request, timeout: FakeResponse(b'{"ok": 1}'))
    assert client.post("http://x/api/embed", {}) == {"ok": 1}


def test_post_http_error_uses_ollama_message_and_hint(monkeypatch):
    def fail(request, timeout):
        body = io.BytesIO(json.dumps({"error": 'model "nope" not found, try pulling it first'}).encode())
        raise HTTPError("http://x", 404, "Not Found", {}, body)

    monkeypatch.setattr(client, "urlopen", fail)
    with pytest.raises(client.OllamaError) as info:
        client.post("http://x/api/embed", {"model": "nope"})
    assert 'model "nope" not found' in str(info.value)
    assert "ollama pull nope" in str(info.value)


def test_post_unreachable(monkeypatch):
    def fail(request, timeout):
        raise URLError("Connection refused")

    monkeypatch.setattr(client, "urlopen", fail)
    with pytest.raises(client.OllamaError, match="ollama serve"):
        client.post("http://x/api/chat", {})


def test_embed_calls_tracer(monkeypatch):
    monkeypatch.setattr(client, "post", lambda url, body, timeout=600: {"embeddings": [[1.0, 0.0]]})
    seen = []
    result = client.embed("m", ["t"], tracer=lambda *a: seen.append(a))
    assert result.vectors == [[1.0, 0.0]]
    assert seen[0][0] == "EMBEDDING MODEL"


def test_chat_result_fields(monkeypatch):
    raw = {
        "message": {"role": "assistant", "content": "Hi [a-1]", "thinking": ""},
        "prompt_eval_count": 12,
        "eval_count": 3,
    }
    monkeypatch.setattr(client, "post", lambda url, body, timeout=600: raw)
    result = client.chat("m", [{"role": "user", "content": "x"}])
    assert (result.content, result.prompt_tokens, result.output_tokens) == ("Hi [a-1]", 12, 3)
    assert result.tool_calls == []


def test_render_prompt_missing_debug_field(monkeypatch):
    monkeypatch.setattr(client, "post", lambda url, body, timeout=600: {"message": {}})
    with pytest.raises(client.OllamaError, match="_debug_render_only"):
        client.render_prompt("m", [])


def test_render_prompt_returns_template(monkeypatch):
    sent = {}

    def fake(url, body, timeout=600):
        sent.update(body)
        return {"_debug_info": {"rendered_template": "<|im_start|>user\nhi"}}

    monkeypatch.setattr(client, "post", fake)
    assert client.render_prompt("m", [{"role": "user", "content": "hi"}]) == "<|im_start|>user\nhi"
    assert sent["_debug_render_only"] is True


def test_chat_moves_inline_thinking_out_of_the_content(monkeypatch):
    # qwen3:4b ignores "think": false and writes its reasoning into the content.
    raw = {"message": {"role": "assistant", "content": "Okay, [x-1] maybe...\n</think>\n\nYes. [a-1]"}}
    monkeypatch.setattr(client, "post", lambda url, body, timeout=600: raw)
    result = client.chat("m", [])
    assert result.content == "Yes. [a-1]"
    assert result.thinking == "Okay, [x-1] maybe..."
    raw["message"]["content"] = "<think>\nhmm\n</think>\nNo."
    assert client.chat("m", []).content == "No."
