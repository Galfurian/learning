"""Copied from unit 04 (04-reranking/src/reranklab/client.py), trimmed to what unit 05 uses. Adds the `format` field (a JSON schema) to chat().

There is no SDK on purpose: the requests and responses are plain JSON, and
seeing them is part of the lesson.
"""

import json
import os
import re
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_EMBED_MODEL = "nomic-embed-text"
DEFAULT_CHAT_MODEL = "qwen3:1.7b"


def ollama_url() -> str:
    """The server, from OLLAMA_HOST like the ollama CLI; the local machine by default."""
    host = os.environ.get("OLLAMA_HOST", "").strip() or "127.0.0.1:11434"
    if not host.startswith(("http://", "https://")):
        host = "http://" + host
    if host.count(":") == 1:  # "http://10.0.0.5" -> default port
        host += ":11434"
    return host.rstrip("/")

# (actor, url, request body, response body), for --verbose.
Tracer = Callable[[str, str, dict[str, Any], dict[str, Any]], None]


class OllamaError(RuntimeError):
    """Ollama rejected the request, or could not be reached."""


def post(url: str, body: dict[str, Any], *, timeout: float = 600) -> dict[str, Any]:
    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except HTTPError as exc:
        # Ollama explains what is wrong in the body: {"error": "..."}.
        try:
            message = json.load(exc).get("error", str(exc))
        except (json.JSONDecodeError, AttributeError):
            message = str(exc)
        missing = re.search(r'model "([^"]+)" not found', message)
        if missing:
            message += f". Run: ollama pull {missing.group(1)}"
        raise OllamaError(message) from exc
    except URLError as exc:
        raise OllamaError(
            f"cannot reach Ollama at {url} ({exc.reason}). Is `ollama serve` running?"
        ) from exc
    except TimeoutError as exc:
        raise OllamaError(
            f"Ollama at {url} did not answer within {timeout:.0f} s. Is the machine busy, or the model too slow there?"
        ) from exc


@dataclass
class EmbedResult:
    vectors: list[list[float]]
    seconds: float
    raw: dict[str, Any]


def embed_body(model: str, texts: Sequence[str]) -> dict[str, Any]:
    return {"model": model, "input": list(texts)}


def embed(model: str, texts: Sequence[str], *, tracer: Tracer | None = None) -> EmbedResult:
    """Turn every text into one vector. Ollama returns unit-length vectors."""
    body = embed_body(model, texts)
    started = time.perf_counter()
    url = f"{ollama_url()}/api/embed"
    raw = post(url, body)
    seconds = time.perf_counter() - started
    if tracer is not None:
        tracer("EMBEDDING MODEL", url, body, raw)
    return EmbedResult(vectors=raw["embeddings"], seconds=seconds, raw=raw)


@dataclass
class ChatResult:
    content: str
    thinking: str
    tool_calls: list[dict[str, Any]]
    message: dict[str, Any]
    prompt_tokens: int
    output_tokens: int
    seconds: float
    raw: dict[str, Any] = field(repr=False)


def chat_body(
    model: str,
    messages: list[dict[str, Any]],
    *,
    think: bool = False,
    num_ctx: int | None = None,
    tools: list[dict[str, Any]] | None = None,
    format: dict[str, Any] | None = None,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    body: dict[str, Any] = {"model": model, "messages": messages, "stream": False, "think": think}
    if tools:
        body["tools"] = tools
    if format:
        # A JSON schema: Ollama constrains the output to match it.
        body["format"] = format
    options = {}
    if num_ctx:
        options["num_ctx"] = num_ctx
    if max_tokens:
        options["num_predict"] = max_tokens   # a small model can loop; this ends the request
    if options:
        body["options"] = options
    return body


def split_thinking(content: str) -> tuple[str, str]:
    """Some models ignore "think": false and write their reasoning before </think>."""
    if "</think>" not in content:
        return content, ""
    thinking, answer = content.rsplit("</think>", 1)
    return answer.strip(), thinking.replace("<think>", "").strip()


def chat(
    model: str,
    messages: list[dict[str, Any]],
    *,
    think: bool = False,
    num_ctx: int | None = None,
    tools: list[dict[str, Any]] | None = None,
    format: dict[str, Any] | None = None,
    max_tokens: int | None = None,
    tracer: Tracer | None = None,
) -> ChatResult:
    body = chat_body(model, messages, think=think, num_ctx=num_ctx, tools=tools, format=format, max_tokens=max_tokens)
    started = time.perf_counter()
    raw = post(f"{ollama_url()}/api/chat", body)
    seconds = time.perf_counter() - started
    if tracer is not None:
        tracer("GENERATIVE MODEL", f"{ollama_url()}/api/chat", body, raw)
    message = raw.get("message", {})
    content, inline = split_thinking(message.get("content", "") or "")
    return ChatResult(
        content=content,
        thinking=(message.get("thinking", "") or "") + inline,
        tool_calls=message.get("tool_calls", []) or [],
        message=message,
        prompt_tokens=raw.get("prompt_eval_count", 0),
        output_tokens=raw.get("eval_count", 0),
        seconds=seconds,
        raw=raw,
    )


def render_prompt(
    model: str,
    messages: list[dict[str, Any]],
    *,
    think: bool = False,
    num_ctx: int | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> str:
    """The exact text the generator reads, after Ollama applies the chat template.

    ``_debug_render_only`` is an undocumented Ollama debug field (verified on
    0.35.0). Ollama renders the template and returns it without generating.
    """
    body = chat_body(model, messages, think=think, num_ctx=num_ctx, tools=tools)
    body["_debug_render_only"] = True
    raw = post(f"{ollama_url()}/api/chat", body)
    try:
        return raw["_debug_info"]["rendered_template"]
    except (KeyError, TypeError):
        raise OllamaError(
            "this Ollama version did not return _debug_info.rendered_template for "
            "_debug_render_only; --show-raw needs it (tested on Ollama 0.35.0)."
        ) from None
