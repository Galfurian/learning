import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp import Client
from mcp.client.stdio import StdioServerParameters
from ollama import AsyncClient

SRC = Path(__file__).resolve().parent


def to_ollama_tool(tool: Any) -> dict[str, Any]:
    """Translate one MCP Tool description into Ollama's function-tool schema."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        },
    }


def tool_result_as_text(result: Any) -> str:
    """Turn an MCP tool result into text that can be fed back to the LLM."""
    if result.structured_content is not None:
        payload = result.structured_content
    else:
        payload = [block.model_dump(mode="json") for block in result.content]
    return json.dumps(payload, ensure_ascii=False)


async def run_agent(prompt: str, model: str, max_steps: int = 8) -> None:
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(SRC / "server.py")],
        cwd=SRC,
    )

    ollama = AsyncClient()

    async with Client(server) as mcp:
        listed = await mcp.list_tools()
        ollama_tools = [to_ollama_tool(tool) for tool in listed.tools]

        print("MCP tools:", ", ".join(tool.name for tool in listed.tools))
        messages: list[Any] = [
            {
                "role": "system",
                "content": (
                    "You are a small local assistant. Use the available tools whenever "
                    "the answer depends on information exposed by them. Do not invent tool results."
                ),
            },
            {"role": "user", "content": prompt},
        ]

        for step in range(1, max_steps + 1):
            response = await ollama.chat(
                model=model,
                messages=messages,
                tools=ollama_tools,
                think=False,
            )
            messages.append(response.message)

            calls = response.message.tool_calls or []
            if not calls:
                print(f"\nAssistant: {response.message.content}")
                return

            for call in calls:
                name = call.function.name
                arguments = dict(call.function.arguments)
                print(f"[step {step}] tool call -> {name}({arguments})")

                result = await mcp.call_tool(name, arguments)
                text = tool_result_as_text(result)
                print(f"[step {step}] tool result <- {text}")

                messages.append(
                    {
                        "role": "tool",
                        "tool_name": name,
                        "content": text,
                    }
                )

        raise RuntimeError(f"Agent exceeded {max_steps} tool-calling steps")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "prompt",
        nargs="?",
        default="What is the internal code for project atlas?",
    )
    parser.add_argument(
        "--model",
        default="qwen3:1.7b",
        help="Any Ollama model installed locally that supports tool calling.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_agent(args.prompt, args.model))
