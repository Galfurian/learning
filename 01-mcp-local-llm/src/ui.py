import json
from pathlib import Path
from typing import Any

from rich.console import Console, Group
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

console = Console()

ROLE_STYLES = {
    "system": "magenta",
    "user": "cyan",
    "assistant": "green",
    "tool": "yellow",
}


def _to_data(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _to_data(value.model_dump(by_alias=True, mode="json"))
    if isinstance(value, dict):
        return {key: _to_data(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_data(item) for item in value]
    return value


def _compact_data(value: Any) -> Any:
    value = _to_data(value)

    if isinstance(value, dict):
        return {
            key: _compact_data(item)
            for key, item in value.items()
            if item is not None
        }

    if isinstance(value, list):
        return [_compact_data(item) for item in value]

    return value


def _json(value: Any) -> Syntax:
    text = json.dumps(
        _compact_data(value),
        ensure_ascii=False,
        indent=2,
        default=str,
    )
    return Syntax(text, "json", word_wrap=True, padding=0)


def _maybe_parse_json(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def _message_bubble(message: Any, *, direction: str) -> None:
    data = _compact_data(message)
    role = str(data.get("role", "message"))
    style = ROLE_STYLES.get(role, "white")
    content = data.get("content", "")
    tool_calls = data.get("tool_calls")
    tool_name = data.get("tool_name")

    parts: list[Any] = []

    if content:
        parsed = _maybe_parse_json(content)
        if isinstance(parsed, (dict, list)):
            parts.append(_json(parsed))
        else:
            parts.append(Text(str(content)))

    if tool_calls:
        if parts:
            parts.append(Text())
        parts.append(Text("tool_calls", style="bold"))
        parts.append(_json(tool_calls))

    if not parts:
        parts.append(Text("<empty content>", style="dim"))

    console.print(
        Panel(
            Group(*parts),
            title=f"{direction} · {role.upper()}",
            subtitle=f"tool={tool_name}" if tool_name else None,
            border_style=style,
            expand=True,
        )
    )


def show_mcp_server(verbose: bool, server_path: Path) -> None:
    if not verbose:
        return

    console.print(
        f"[bold blue]MCP server[/bold blue] "
        f"[dim]stdio -> {server_path}[/dim]"
    )
    console.print(
        "[bold blue]HOST -> MCP[/bold blue] "
        "[dim]tools/list[/dim]"
    )


def show_discovered_tools(verbose: bool, tools: list[Any]) -> None:
    if not verbose:
        console.print(
            "MCP tools:",
            ", ".join(tool.name for tool in tools),
        )
        return

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
    if not verbose:
        return

    console.rule(
        f"[bold]OLLAMA REQUEST · step {step}[/bold] "
        f"[dim]model={model} · messages={len(messages)} · tools={tool_count}[/dim]"
    )

    for message in messages:
        _message_bubble(message, direction="HOST -> OLLAMA")


def show_ollama_response(verbose: bool, message: Any) -> None:
    if verbose:
        _message_bubble(message, direction="OLLAMA -> HOST")


def show_tool_call(
    verbose: bool,
    step: int,
    name: str,
    arguments: dict[str, Any],
) -> None:
    if verbose:
        console.print(
            Panel(
                _json(arguments),
                title=f"HOST -> MCP · tools/call · {name}",
                border_style="blue",
                expand=True,
            )
        )
        return

    console.print(f"[step {step}] tool call -> {name}({arguments})")


def show_tool_result(
    verbose: bool,
    step: int,
    name: str,
    payload: Any,
) -> None:
    if verbose:
        console.print(
            Panel(
                _json(payload),
                title=f"MCP -> HOST · result · {name}",
                border_style="bright_blue",
                expand=True,
            )
        )
        console.print(
            "[dim]HOST appends this result as a TOOL message; "
            "it will appear in the next Ollama request.[/dim]"
        )
        return

    console.print(
        f"[step {step}] tool result <- "
        f"{json.dumps(payload, ensure_ascii=False)}"
    )


def show_final_answer(content: str) -> None:
    console.print(f"\nAssistant: {content}")
