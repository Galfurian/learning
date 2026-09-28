import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp import Client
from mcp.client.stdio import StdioServerParameters
from ollama import AsyncClient
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.text import Text

SRC = Path(__file__).resolve().parent
console = Console()

ROLE_STYLES = {
    "system": "magenta",
    "user": "cyan",
    "assistant": "green",
    "tool": "yellow",
}


def to_data(value: Any) -> Any:
    """Recursively turn SDK/Pydantic objects into JSON-friendly data."""
    if hasattr(value, "model_dump"):
        return to_data(value.model_dump(by_alias=True, mode="json"))
    if isinstance(value, dict):
        return {key: to_data(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_data(item) for item in value]
    return value


def json_renderable(value: Any) -> JSON:
    """Pretty JSON renderable used inside Rich panels."""
    return JSON.from_data(to_data(value), ensure_ascii=False)


def trace_panel(
    verbose: bool,
    title: str,
    value: Any | None = None,
    *,
    border_style: str = "blue",
    subtitle: str | None = None,
) -> None:
    """Render one protocol/adapter step when --verbose is enabled."""
    if not verbose:
        return

    body: Any
    if value is None:
        body = Text("request")
    else:
        body = json_renderable(value)

    console.print(
        Panel(
            body,
            title=title,
            subtitle=subtitle,
            border_style=border_style,
            expand=False,
        )
    )


def message_bubble(
    verbose: bool,
    message: Any,
    *,
    direction: str,
) -> None:
    """Render a complete LLM conversation message as a colored bubble."""
    if not verbose:
        return

    data = to_data(message)
    role = str(data.get("role", "message")) if isinstance(data, dict) else "message"
    style = ROLE_STYLES.get(role, "white")

    console.print(
        Panel(
            json_renderable(data),
            title=f"{direction} · {role.upper()}",
            border_style=style,
            expand=False,
        )
    )


def show_ollama_request(
    verbose: bool,
    *,
    step: int,
    model: str,
    messages: list[Any],
    tools: list[dict[str, Any]],
) -> None:
    if not verbose:
        return

    console.rule(f"[bold]OLLAMA REQUEST · step {step}[/bold]")
    trace_panel(
        True,
        "HOST -> OLLAMA · request metadata",
        {
            "model": model,
            "think": False,
            "message_count": len(messages),
            "tool_count": len(tools),
        },
        border_style="bright_blue",
    )

    console.print("[bold]Messages sent to Ollama[/bold]")
    for message in messages:
        message_bubble(True, message, direction="HOST -> OLLAMA")

    trace_panel(
        True,
        "HOST -> OLLAMA · tool schemas",
        tools,
        border_style="bright_blue",
    )


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


def tool_result_as_text(result: Any) -> str:
    """Turn an MCP tool result into text that can be fed back to the LLM."""
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

    trace_panel(
        verbose,
        "HOST · MCP stdio server configuration",
        {
            "command": server.command,
            "args": server.args,
            "cwd": str(server.cwd),
        },
        border_style="blue",
    )

    ollama = AsyncClient()

    async with Client(server) as mcp:
        trace_panel(
            verbose,
            "HOST -> MCP · tools/list",
            {"method": "tools/list"},
            border_style="blue",
        )
        listed = await mcp.list_tools()

        mcp_tools = [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
            }
            for tool in listed.tools
        ]
        trace_panel(
            verbose,
            "MCP -> HOST · tools/list result",
            mcp_tools,
            border_style="bright_blue",
        )

        ollama_tools = [to_ollama_tool(tool) for tool in listed.tools]
        trace_panel(
            verbose,
            "HOST · MCP -> Ollama schema translation",
            ollama_tools,
            border_style="bright_magenta",
        )

        console.print(
            "MCP tools:",
            ", ".join(tool.name for tool in listed.tools),
        )

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
            show_ollama_request(
                verbose,
                step=step,
                model=model,
                messages=messages,
                tools=ollama_tools,
            )

            response = await ollama.chat(
                model=model,
                messages=messages,
                tools=ollama_tools,
                think=False,
            )

            message_bubble(
                verbose,
                response.message,
                direction="OLLAMA -> HOST",
            )
            messages.append(response.message)

            calls = response.message.tool_calls or []
            if not calls:
                console.print(f"\nAssistant: {response.message.content}")
                return

            for call in calls:
                name = call.function.name
                arguments = dict(call.function.arguments)

                trace_panel(
                    verbose,
                    "OLLAMA -> HOST · requested tool call",
                    {"name": name, "arguments": arguments},
                    border_style="green",
                )
                console.print(f"[step {step}] tool call -> {name}({arguments})")

                trace_panel(
                    verbose,
                    "HOST -> MCP · tools/call",
                    {
                        "method": "tools/call",
                        "name": name,
                        "arguments": arguments,
                    },
                    border_style="blue",
                )
                result = await mcp.call_tool(name, arguments)
                trace_panel(
                    verbose,
                    "MCP -> HOST · tools/call result",
                    result,
                    border_style="bright_blue",
                )

                text = tool_result_as_text(result)
                console.print(f"[step {step}] tool result <- {text}")

                tool_message = {
                    "role": "tool",
                    "tool_name": name,
                    "content": text,
                }
                messages.append(tool_message)

                message_bubble(
                    verbose,
                    tool_message,
                    direction="HOST queues for OLLAMA",
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
            "Render the complete MCP/Ollama exchange as colored Rich panels, "
            "including every conversation message."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_agent(args.prompt, args.model, args.verbose))
