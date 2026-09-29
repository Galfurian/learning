import json
from typing import Any


def to_ollama_tool(tool: Any) -> dict[str, Any]:
    """Translate one MCP tool definition into Ollama's function-tool schema."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        },
    }


def tool_result_payload(result: Any) -> Any:
    """Extract the meaningful part of an MCP tool result."""
    if result.structured_content is not None:
        return result.structured_content

    return [
        block.model_dump(mode="json")
        for block in result.content
    ]


def tool_message_from_result(
    tool_name: str,
    result: Any,
) -> tuple[dict[str, Any], Any]:
    """Build the Ollama role=tool message from an MCP result."""
    payload = tool_result_payload(result)

    message = {
        "role": "tool",
        "tool_name": tool_name,
        "content": json.dumps(payload, ensure_ascii=False),
    }

    return message, payload
