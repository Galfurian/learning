import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any

from mcp import Client
from mcp.client.stdio import StdioServerParameters
from ollama import AsyncClient
from rich.console import Console, Group
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
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
    """Recursively turn SDK/Pydantic objects into plain Python data."""
    if hasattr(value, "model_dump"):
        return to_data(value.model_dump(by_alias=True, mode="json"))
    if isinstance(value, dict):
        return {key: to_data(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_data(item) for item in value]
    return value


def compact_data(value: Any) -> Any:
    """Remove SDK noise such as null fields while preserving meaningful values."""
    value = to_data(value)

    if isinstance(value, dict):
        return {
            key: compact_data(item)
            for key, item in value.items()
            if item is not None
        }

    if isinstance(value, list):
        return [compact_data(item) for item in value]

    return value


def json_renderable(value: Any) -> Syntax:
    """Pretty JSON that wraps inside the terminal width."""
    text = json.dumps(
        compact_data(value),
        ensure_ascii=False,
        indent=2,
        default=str,
    )
    return Syntax(text, "json", word_wrap=True, padding=0)


def parse_json_string(value: Any) -> Any:
    """Parse JSON stored inside a string only for prettier display."""
    if not isinstance(value, str):
        return value

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def message_bubble(
    verbose: bool,
    message: Any,
    *,
    direction: str,
) -> None:
    """Render one complete LLM message without irrelevant SDK null fields."""
    if not verbose:
        return

    data = compact_data(message)
    role = str(data.get("role", "message"))
    style = ROLE_STYLES.get(role, "white")
    content = data.get("content", "")
    tool_calls = data.get("tool_calls")
    tool_name = data.get("tool_name")

    parts: list[Any] = []

    if content:
        parsed_content = parse_json_string(content)
        if isinstance(parsed_content, (dict, list)):
            parts.append(json_renderable(parsed_content))
        else:
            parts.append(Text(str(content)))

    if tool_calls:
        if parts:
            parts.append(Text())
        parts.append(Text("tool_calls", style="bold"))
        parts.append(json_renderable(tool_calls))

    if not parts:
        parts.append(Text("<empty content>", style="dim"))

    subtitle = f"tool={tool_name}" if tool_name else None

    console.print(
        Panel(
            Group(*parts),
            title=f"{direction} · {role.upper()}",
            subtitle=subtitle,
            border_style=style,
            expand=True,
        )
    )


def show_discovered_tools(tools: list[Any]) -> None:
    """Show the useful result of MCP tools/list without dumping the full SDK payload."""
    table = Table(
        title="MCP tools discovered via tools/list",
        show_header=True,
        header_style="bold",
        expand=True,
    )
    table.add_column("Tool")
    table.add_column("Description")
    table.add_column("Input schema")

    for tool in tools:
        table.add_row(
            tool.name,
            (tool.description or "").strip(),
            json.dumps(tool.input_schema, ensure_ascii=False),
        )

    console.print(table)


def show_ollama_request(
    verbose: bool,
    *,
    step: int,
    model: str,
    messages: list[Any],
    tool_count: int,
) -> None:
    """Show exactly the conversation history that is sent to Ollama."""
    if not verbose:
        return

    console.rule(
        f"[bold]OLLAMA REQUEST · step {step}[/bold] "
        f"[dim]model={model} · messages={len(messages)} · tools={tool_count}[/dim]"
    )

    for message in messages:
        message_bubble(True, message, direction="HOST -> OLLAMA")


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
    """Extract the meaningful tool result that will be sent back to the model."""
    if result.structured_content is not None:
        return result.structured_content
    return [block.model_dump(mode="json") for block in result.content]


def tool_result_as_text(result: Any) -> str:
    return json.dumps(tool_result_payload(result), ensure_ascii=False)


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

    if verbose:
        console.print(
            f"[bold blue]MCP server[/bold blue] "
            f"[dim]stdio -> {SRC / 'server.py'}[/dim]"
        )
        console.print("[bold blue]HOST -> MCP[/bold blue] [dim]tools/list[/dim]")

    ollama = AsyncClient()

    async with Client(server) as mcp:
        listed = await mcp.list_tools()

        if verbose:
            show_discovered_tools(listed.tools)

        ollama_tools = [to_ollama_tool(tool) for tool in listed.tools]

        if not verbose:
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
                tool_count=len(ollama_tools),
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

                if verbose:
                    console.print(
                        Panel(
                            json_renderable(arguments),
                            title=f"HOST -> MCP · tools/call · {name}",
                            border_style="blue",
                            expand=True,
                        )
                    )
                else:
                    console.print(
                        f"[step {step}] tool call -> {name}({arguments})"
                    )

                result = await mcp.call_tool(name, arguments)
                payload = tool_result_payload(result)

                if verbose:
                    console.print(
                        Panel(
                            json_renderable(payload),
                            title=f"MCP -> HOST · result · {name}",
                            border_style="bright_blue",
                            expand=True,
                        )
                    )
                else:
                    console.print(
                        f"[step {step}] tool result <- "
                        f"{json.dumps(payload, ensure_ascii=False)}"
                    )

                tool_message = {
                    "role": "tool",
                    "tool_name": name,
                    "content": json.dumps(payload, ensure_ascii=False),
                }
                messages.append(tool_message)

                if verbose:
                    console.print(
                        "[dim]HOST appends the TOOL message to the conversation; "
                        "it will appear in the next Ollama request.[/dim]"
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
            "Show the educational MCP/Ollama flow with complete conversation "
            "messages and only the protocol payloads that matter."
        ),
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    asyncio.run(run_agent(args.prompt, args.model, args.verbose))
