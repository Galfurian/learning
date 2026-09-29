import json
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


def _event_line(event: str) -> Text:
    text = Text()
    text.append("Event: ", style="bold")
    text.append(event)
    return text


def _panel(
    source: str,
    target: str,
    event: str,
    body: Any | None = None,
    *,
    border_style: str = "blue",
) -> None:
    parts: list[Any] = [_event_line(event)]

    if body is not None:
        parts.append(Text())
        parts.append(body)

    console.print(
        Panel(
            Group(*parts),
            title=f"{source} -> {target}",
            border_style=border_style,
            expand=True,
        )
    )


def _message_bubble(
    message: Any,
    *,
    source: str,
    target: str,
) -> None:
    data = _compact_data(message)
    role = str(data.get("role", "message"))
    style = ROLE_STYLES.get(role, "white")
    content = data.get("content", "")
    tool_calls = data.get("tool_calls")
    tool_name = data.get("tool_name")

    parts: list[Any] = [
        _event_line(
            f"conversation message · role={role}"
            + (f" · tool={tool_name}" if tool_name else "")
        )
    ]

    if content:
        parts.append(Text())
        parsed = _maybe_parse_json(content)
        if isinstance(parsed, (dict, list)):
            parts.append(_json(parsed))
        else:
            parts.append(Text(str(content)))

    if tool_calls:
        parts.append(Text())
        parts.append(Text("tool_calls", style="bold"))
        parts.append(_json(tool_calls))

    if not content and not tool_calls:
        parts.append(Text())
        parts.append(Text("<empty content>", style="dim"))

    console.print(
        Panel(
            Group(*parts),
            title=f"{source} -> {target}",
            border_style=style,
            expand=True,
        )
    )


def _show_actors(model: str, server_label: str) -> None:
    table = Table(
        title="Actors",
        show_header=True,
        header_style="bold",
        expand=True,
    )
    table.add_column("Actor")
    table.add_column("Meaning")

    table.add_row(
        "HOST",
        "mcplab.agent: orchestrates the loop, executes MCP calls, and maintains conversation history.",
    )
    table.add_row(
        "OLLAMA",
        (
            f"Local runtime/API running {model}. The model decides whether to emit "
            "tool_calls and their arguments; Ollama returns that model output to HOST."
        ),
    )
    table.add_row(
        "MCP SERVER",
        f"{server_label}: exposes tools and executes them when HOST sends MCP tools/call.",
    )

    console.print(table)
    console.print(
        "[dim]Conversation roles (system/user/assistant/tool) are message roles, "
        "not additional actors.[/dim]\n"
    )


def show_mcp_server(verbose: bool, server_label: str, model: str) -> None:
    if not verbose:
        return

    _show_actors(model, server_label)

    _panel(
        "HOST",
        "MCP SERVER",
        f"start/connect over stdio · {server_label}",
        border_style="blue",
    )
    _panel(
        "HOST",
        "MCP SERVER",
        "MCP tools/list",
        border_style="blue",
    )


def show_discovered_tools(
    verbose: bool,
    tools: list[Any],
    *,
    quiet: bool = False,
) -> None:
    if not verbose:
        if not quiet:
            console.print(
                "MCP tools:",
                ", ".join(tool.name for tool in tools),
            )
        return

    table = Table(
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

    _panel(
        "MCP SERVER",
        "HOST",
        "MCP tools/list result · discovered tool contracts",
        table,
        border_style="bright_blue",
    )


def show_attached_resource(
    verbose: bool,
    uri: str,
    text: str,
    *,
    quiet: bool = False,
) -> None:
    if verbose:
        _panel(
            "HOST",
            "MCP SERVER",
            f"MCP resources/read · {uri}",
            border_style="blue",
        )
        _panel(
            "MCP SERVER",
            "HOST",
            f"MCP resources/read result · {uri}",
            Text(text),
            border_style="bright_blue",
        )
        console.print(
            "[dim]HOST chose to attach this resource: it is appended to the "
            "system message. The model never requested it.[/dim]"
        )
        return

    if not quiet:
        console.print(f"MCP resource attached: {uri}")


def show_missing_resource(uri: str, error: Exception) -> None:
    console.print(
        f"[red]MCP resource not attached: {uri} ({error}). "
        "The model answers without it.[/red]"
    )


def _show_step_context(
    step: int,
    messages: list[Any],
) -> None:
    has_tool_result = any(
        isinstance(_compact_data(message), dict)
        and _compact_data(message).get("role") == "tool"
        for message in messages
    )

    if has_tool_result:
        purpose = (
            "Continue the model inference with tool result(s) now present in the "
            "conversation; the model may answer or request another tool."
        )
    else:
        purpose = (
            "Run the initial model inference on the user's request and the available "
            "tool contracts; the model may answer directly or request a tool."
        )

    console.print(
        "[bold]Participants:[/bold] HOST <-> OLLAMA; "
        "MCP SERVER joins this step only if the model emits tool_calls."
    )
    console.print(f"[bold]Purpose:[/bold] {purpose}")
    console.print(
        "[dim]Step boundary: one Ollama inference round plus any MCP tool execution "
        "requested by that round. The next step starts when HOST calls Ollama again.[/dim]\n"
    )


def show_model_input(step: int, rendered_prompt: str) -> None:
    console.rule(f"[bold]MODEL INPUT · step {step}[/bold]")
    console.print(
        Panel(
            Group(
                _event_line(
                    "rendered chat template · exact prompt string before tokenization"
                ),
                Text(),
                Text(rendered_prompt),
            ),
            title="OLLAMA -> MODEL",
            subtitle="special BOS handling may occur separately from this string",
            border_style="bright_magenta",
            expand=True,
        )
    )


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
        f"[bold]STEP {step}[/bold] "
        f"[dim]model={model} · messages={len(messages)} · tools={tool_count}[/dim]"
    )
    _show_step_context(step, messages)

    for message in messages:
        _message_bubble(
            message,
            source="HOST",
            target="OLLAMA",
        )


def show_ollama_response(verbose: bool, message: Any) -> None:
    if verbose:
        _message_bubble(
            message,
            source="OLLAMA",
            target="HOST",
        )


def show_tool_call(
    verbose: bool,
    step: int,
    name: str,
    arguments: dict[str, Any],
    *,
    quiet: bool = False,
) -> None:
    if verbose:
        _panel(
            "HOST",
            "MCP SERVER",
            f"MCP tools/call · {name}",
            _json(arguments),
            border_style="blue",
        )
        return

    if not quiet:
        console.print(f"[step {step}] tool call -> {name}({arguments})")


def show_tool_result(
    verbose: bool,
    step: int,
    name: str,
    payload: Any,
    *,
    quiet: bool = False,
) -> None:
    if verbose:
        _panel(
            "MCP SERVER",
            "HOST",
            f"MCP tools/call result · {name}",
            _json(payload),
            border_style="bright_blue",
        )
        console.print(
            "[dim]HOST appends this result as a role=tool message; "
            "that message appears in the next HOST -> OLLAMA exchange.[/dim]"
        )
        return

    if not quiet:
        console.print(
            f"[step {step}] tool result <- "
            f"{json.dumps(payload, ensure_ascii=False)}"
        )


def show_final_answer(content: str) -> None:
    console.print(f"\nAssistant: {content}")
