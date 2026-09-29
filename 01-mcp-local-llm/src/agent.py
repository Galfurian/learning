import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any

from mcp import Client
from mcp.client.stdio import StdioServerParameters
from ollama import AsyncClient

from bridge import to_ollama_tool, tool_message_from_result
from model_io import render_model_input
from ui import (
    show_discovered_tools,
    show_final_answer,
    show_mcp_server,
    show_model_input,
    show_ollama_request,
    show_ollama_response,
    show_tool_call,
    show_tool_result,
)

SRC = Path(__file__).resolve().parent


async def run_agent(
    prompt: str,
    model: str,
    verbose: bool,
    show_raw: bool,
    max_steps: int = 8,
) -> None:
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(SRC / "server.py")],
        cwd=SRC,
    )
    show_mcp_server(verbose, SRC / "server.py", model)

    ollama = AsyncClient()

    async with Client(server) as mcp:
        listed = await mcp.list_tools()
        show_discovered_tools(
            verbose,
            listed.tools,
            quiet=show_raw,
        )

        ollama_tools = [to_ollama_tool(tool) for tool in listed.tools]

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
            if show_raw:
                rendered = await render_model_input(
                    model,
                    messages,
                    ollama_tools,
                )
                show_model_input(step, rendered)

            show_ollama_request(
                verbose,
                step=step,
                model=model,
                messages=messages,
                tool_count=len(ollama_tools),
            )

            response = await ollama.chat(
                model=model,
                messages=messages,
                tools=ollama_tools,
                think=False,
            )

            show_ollama_response(verbose, response.message)
            messages.append(response.message)

            calls = response.message.tool_calls or []
            if not calls:
                show_final_answer(response.message.content)
                return

            for call in calls:
                name = call.function.name
                arguments = dict(call.function.arguments)

                show_tool_call(
                    verbose,
                    step,
                    name,
                    arguments,
                    quiet=show_raw,
                )

                result = await mcp.call_tool(name, arguments)
                tool_message, payload = tool_message_from_result(name, result)

                show_tool_result(
                    verbose,
                    step,
                    name,
                    payload,
                    quiet=show_raw,
                )
                messages.append(tool_message)

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
    trace_group = parser.add_mutually_exclusive_group()
    trace_group.add_argument(
        "--verbose",
        action="store_true",
        help=(
            "Show the educational MCP/Ollama flow with complete conversation "
            "messages and only the protocol payloads that matter."
        ),
    )
    trace_group.add_argument(
        "--show-raw",
        action="store_true",
        help=(
            "Show only the rendered prompt string Ollama prepares for the model "
            "before each inference round."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(
        run_agent(
            args.prompt,
            args.model,
            args.verbose,
            args.show_raw,
        )
    )
