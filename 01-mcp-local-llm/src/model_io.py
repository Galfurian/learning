import asyncio
import json
from typing import Any
from urllib.request import Request, urlopen

OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"


def _jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _jsonable(value.model_dump(by_alias=True, mode="json"))
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    return value


def _render_model_input_sync(
    model: str,
    messages: list[Any],
    tools: list[dict[str, Any]],
) -> str:
    payload = {
        "model": model,
        "messages": _jsonable(messages),
        "tools": _jsonable(tools),
        "think": False,
        "stream": False,
        "_debug_render_only": True,
    }

    request = Request(
        OLLAMA_CHAT_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urlopen(request) as response:
        body = json.load(response)

    try:
        return body["_debug_info"]["rendered_template"]
    except KeyError as exc:
        raise RuntimeError(
            "This Ollama version did not return _debug_info.rendered_template. "
            "The --show-model-input mode relies on Ollama's internal "
            "_debug_render_only option."
        ) from exc


async def render_model_input(
    model: str,
    messages: list[Any],
    tools: list[dict[str, Any]],
) -> str:
    """Ask Ollama to render the chat template without running the model."""
    return await asyncio.to_thread(
        _render_model_input_sync,
        model,
        messages,
        tools,
    )
