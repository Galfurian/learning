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


def pretty(value: Any) -> str:
    if hasattr(value, "model_dump"):
        value = value.model_dump(by_alias=True, mode="json")
    return json.dumps(value, ensure_ascii=False, indent=2, default=str)


def trace(verbose: bool, title: str, value: Any | None = None) -> None:
    if not verbose:
        return
    print(f"\n=== {title} ===")
    if value is not None:
        print(pretty(value))


def to_ollama_tool(tool: Any) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        },
    }


def tool_result_as_text(result: Any) -> str:
    if result.structured_content is not None:
        payload = result.structured_content
    else:
        payload = [block.model_dump(mode="json") for block in result.content]
    return json.dumps(payload, ensure_ascii=False)


async def run_agent(
    prompt: str,
    model: str,
    verbose: bool,
    max_steps: int = 8,
) -> None:
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(SRC / "server.py")],
        cwd=SRC,
    )

    trace(verbose, "1. MCP stdio server configuration", {
        "command": server.command,
        "args": server.args,
        "cwd": str(server.cwd),
    })

    ollama = AsyncClient()

    async with Client(server) as mcp:
        trace(verbose, "2. MCP request: tools/list")
        listed = await mcp.list_tools()

        mcp_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            }
            for tool in listed.tools
        ]
        trace(verbose, "3. MCP response: discovered tools", mcp_tools)

        ollama_tools = [to_ollama_tool(tool) for tool in listed.tools]
        trace(verbose, "4. MCP -> Ollama tool-schema translation", ollama_tools)

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
            trace(verbose, f"5.{step}. Request to Ollama", {
                "model": model,
                "messages": messages,
                "tools": ollama_tools,
                "think": False,
            })

            response = await ollama.chat(
                model=model,
                messages=messages,
                tools=ollama_tools,
                think=False,
            )

            trace(verbose, f"6.{step}. Response from Ollama", response.message)
            messages.append(response.message)

            calls = response.message.tool_calls or []
            if not calls:
                print(f"\nAssistant: {response.message.content}")
                return

            for call in calls:
                name = call.function.name
                arguments = dict(call.function.arguments)

                trace(verbose, f"7.{step}. Model requested a tool call", {
                    "name": name,
                    "arguments": arguments,
                })
                print(f"[step {step}] tool call -> {name}({arguments})")

                trace(verbose, f"8.{step}. MCP request: tools/call", {
                    "name": name,
                    "arguments": arguments,
                })
                result = await mcp.call_tool(name, arguments)
                trace(verbose, f"9.{step}. MCP response: tool result", result)

                text = tool_result_as_text(result)
                print(f"[step {step}] tool result <- {text}")

                tool_message = {
                    "role": "tool",
                    "tool_name": name,
                    "content": text,
                }
                messages.append(tool_message)
                trace(
                    verbose,
                    f"10.{step}. Tool result appended to LLM conversation",
                    tool_message,
                )

        raise RuntimeError(f"Agent exceeded {max_steps} tool-calling steps")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ask a local Ollama model a question using tools discovered through MCP."
    )
    parser.add_argument(
        "prompt",
        help="Question to send to the local model. There is intentionally no default prompt.",
    )
    parser.add_argument(
        "--model",
        default="qwen3:1.7b",
        help="Any Ollama model installed locally that supports tool calling.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help=(
            "Show MCP discovery, schema translation, Ollama messages, "
            "tool calls, MCP results, and the feedback loop."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_agent(args.prompt, args.model, args.verbose))
