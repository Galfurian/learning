import json
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from rich.console import Console, Group
from rich.live import Live
from rich.markdown import Markdown
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
    thinking = data.get("thinking")
    tool_calls = data.get("tool_calls")
    tool_name = data.get("tool_name")

    parts: list[Any] = [
        _event_line(
            f"conversation message · role={role}"
            + (f" · tool={tool_name}" if tool_name else "")
        )
    ]

    if thinking:
        parts.append(Text())
        parts.append(Text("thinking", style="bold"))
        parts.append(Text(str(thinking).strip(), style="dim italic"))

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

    if not content and not tool_calls and not thinking:
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


def show_mcp_prompt(
    verbose: bool,
    name: str,
    arguments: dict[str, str],
    messages: list[dict[str, str]],
) -> None:
    call = f"{name}({', '.join(f'{k}={v!r}' for k, v in arguments.items())})"
    text = "\n\n".join(f"[{m['role']}] {m['content']}" for m in messages)
    if verbose:
        _panel("HOST", "MCP SERVER", f"MCP prompts/get · {call}", border_style="blue")
        _panel("MCP SERVER", "HOST", f"MCP prompts/get result · {call}", Text(text),
               border_style="bright_blue")
        console.print(
            "[dim]HOST uses these messages as the user's request, instead of a typed prompt.[/dim]"
        )
        return
    show_user_message(text, source=f"MCP prompt {call}")


def show_resource_catalog(
    verbose: bool,
    resources: list[Any],
    *,
    quiet: bool = False,
) -> None:
    if not verbose:
        if not quiet:
            console.print(
                "MCP resources (listed, not loaded):",
                ", ".join(str(resource.uri) for resource in resources) or "none",
            )
        return

    _panel(
        "HOST",
        "MCP SERVER",
        "MCP resources/list",
        border_style="blue",
    )

    table = Table(show_header=True, header_style="bold", expand=True)
    table.add_column("URI")
    table.add_column("Description")
    for resource in resources:
        table.add_row(str(resource.uri), resource.description or resource.name)

    _panel(
        "MCP SERVER",
        "HOST",
        "MCP resources/list result · metadata only, no content",
        table,
        border_style="bright_blue",
    )
    console.print(
        "[dim]HOST puts only this list in the system message and adds its own "
        "tool read_resource. Content is read only if the model asks.[/dim]"
    )


def show_resource_request(
    verbose: bool,
    step: int,
    uri: str,
    *,
    quiet: bool = False,
) -> None:
    if verbose:
        _panel(
            "HOST",
            "MCP SERVER",
            f"MCP resources/read · {uri} · requested by the model via host tool read_resource",
            border_style="blue",
        )
        return

    # Chat mode shows request and result together, in show_resource_result.


def show_resource_result(
    verbose: bool,
    step: int,
    uri: str,
    content: str,
    *,
    quiet: bool = False,
) -> None:
    if verbose:
        _panel(
            "MCP SERVER",
            "HOST",
            f"MCP resources/read result · {uri}",
            Text(content),
            border_style="bright_blue",
        )
        console.print(
            "[dim]HOST appends this content as a role=tool message: from now on "
            "it is part of the model's context.[/dim]"
        )
        return

    if not quiet:
        console.print(
            Panel(
                Group(
                    Text("host tool read_resource -> MCP resources/read", style="bold"),
                    _brief_text(content),
                ),
                title=f"Resource · {uri}",
                title_align="left",
                border_style="yellow",
            )
        )


def show_context_summary(
    exposed: list[Any],
    templates: list[Any],
    loaded: list[str],
) -> None:
    uris = [str(resource.uri) for resource in exposed]
    patterns = [template.uri_template for template in templates]
    console.print(
        f"\n[bold]Resources exposed by the server:[/bold] {len(uris)} static"
        + (f" ({', '.join(uris)})" if uris else "")
        + (f", {len(patterns)} template(s) ({', '.join(patterns)})" if patterns else "")
    )
    console.print(
        f"[bold]Resources loaded into the model's context:[/bold] {len(loaded)}"
        + (f" ({', '.join(loaded)})" if loaded else "")
    )


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

    # Chat mode shows call and result together, in show_tool_result.


def show_tool_result(
    verbose: bool,
    step: int,
    name: str,
    payload: Any,
    elapsed_s: float,
    *,
    arguments: dict[str, Any] | None = None,
    error: bool = False,
    quiet: bool = False,
) -> None:
    if verbose:
        _panel(
            "MCP SERVER",
            "HOST",
            f"MCP tools/call result · {name} · {duration(elapsed_s)}",
            _json(payload),
            border_style="bright_blue",
        )
        console.print(
            "[dim]HOST appends this result as a role=tool message; "
            "that message appears in the next HOST -> OLLAMA exchange.[/dim]"
        )
        return

    if not quiet:
        args = "  ".join(f"{key}={value}" for key, value in (arguments or {}).items())
        console.print(
            Panel(
                Group(Text(args or "(no arguments)", style="bold"), _brief(payload, error)),
                title=f"Tool · {name} · {duration(elapsed_s)}",
                title_align="left",
                border_style="red" if error else "yellow",
            )
        )


def duration(seconds: float) -> str:
    """Human-readable duration: '0.02s', '12.3s', '2m 57s'."""
    if seconds < 1:
        return f"{seconds:.2f}s"
    if seconds < 60:
        return f"{seconds:.1f}s"
    minutes, rest = divmod(round(seconds), 60)
    return f"{minutes}m {rest:02d}s"


def show_context_usage(
    step: int,
    prompt_tokens: int,
    output_tokens: int,
    num_ctx: int | None,
    truncated: bool,
    thinking_chars: int,
    model_s: float,
    prompt_s: float,
    output_s: float,
    elapsed_s: float,
) -> None:
    used = prompt_tokens + output_tokens
    window = f"{num_ctx:,}" if num_ctx else "Ollama default"
    share = f" ({used / num_ctx:.0%})" if num_ctx else ""
    line = (
        f"step {step} · context: {prompt_tokens:,} prompt + {output_tokens:,} output "
        f"= {used:,} / {window} tokens{share}"
    )
    if thinking_chars:
        line += f" · thought {thinking_chars:,} chars"
    line += (
        f" · model {duration(model_s)} (prompt {duration(prompt_s)}, output {duration(output_s)})"
        f" · elapsed {duration(elapsed_s)}"
    )
    console.print(f"[dim]{line}[/dim]")
    if truncated:
        console.print(
            f"[bold red]\\[step {step}] the conversation no longer fits: Ollama dropped part "
            "of it. Raise --num-ctx.[/bold red]"
        )


def show_answer_check(step: int, feedback: str | None, answer: str, retry: bool) -> None:
    if feedback is None:
        console.print(f"[green]step {step} · host check: answer accepted[/green]")
        return
    if not retry:
        console.print(
            Panel(Text(feedback), title="Host check failed again · no retries left, "
                  "showing the answer anyway", title_align="left", border_style="red")
        )
        return
    console.print(
        Panel(Markdown(answer.strip() or "(empty)"), title="Assistant · rejected by the host check",
              title_align="left", border_style="grey50")
    )
    console.print(
        Panel(Text(feedback), title="Host -> model", title_align="left", border_style="yellow")
    )


def show_skipped_call(
    verbose: bool,
    step: int,
    name: str,
    arguments: dict[str, Any],
    *,
    quiet: bool = False,
) -> None:
    if quiet:
        return
    console.print(
        f"[dim]step {step} · tool call skipped (one per step) -> {name}({arguments})[/dim]"
    )


def show_run_summary(
    total_s: float,
    model_s: float,
    tools_s: float,
    steps: int,
    tool_calls: int,
) -> None:
    console.print(
        f"\n[bold]Done in {duration(total_s)}[/bold] · {steps} model call(s): "
        f"{duration(model_s)} · {tool_calls} tool call(s): {duration(tools_s)} · "
        f"other (startup, MCP discovery): {duration(max(total_s - model_s - tools_s, 0))}"
    )


VERDICT_STYLES = {"✓": "green", "~": "yellow", "✗": "red"}


def show_grade(rows: list[tuple[str, str, str]]) -> None:
    """Score of the final answer against the known truth. Only for humans."""
    table = Table(show_header=True, header_style="bold", expand=True, box=None)
    table.add_column("Aspect")
    table.add_column("", width=2)
    table.add_column("Note")
    for aspect, verdict, note in rows:
        table.add_row(aspect, Text(verdict, style=VERDICT_STYLES.get(verdict, "")), note)
    points = sum({"✓": 1.0, "~": 0.5}.get(verdict, 0.0) for _, verdict, _ in rows)
    console.print(
        Panel(table, title=f"Grade · {points:g}/{len(rows)} · not shown to the model",
              title_align="left", border_style="magenta")
    )


def show_final_answer(content: str) -> None:
    console.print(
        Panel(Markdown(content.strip() or "(empty)"), title="Assistant", title_align="left",
              border_style="green")
    )


# --- chat view: the default mode, neither --verbose nor --show-raw ------------------


def _clip(line: str, width: int = 110) -> str:
    return line if len(line) <= width else line[: width - 1] + "…"


def _brief_text(text: str, lines: int = 3) -> Text:
    """First lines of a long text, and how many are left out."""
    rows = text.strip().splitlines()
    shown = "\n".join(_clip(row) for row in rows[:lines])
    if len(rows) > lines:
        shown += f"\n… (+{len(rows) - lines} more lines)"
    return Text(shown, style="dim")


def _brief(payload: Any, error: bool) -> Text:
    """A few lines that tell what a tool returned, without dumping it."""
    if error:
        text = " ".join(
            block.get("text", "") for block in payload if isinstance(block, dict)
        ) if isinstance(payload, list) else str(payload)
        return Text("error: " + _clip(text, 300), style="red")
    if isinstance(payload, dict) and set(payload) == {"result"}:
        payload = payload["result"]
    if isinstance(payload, str):
        return _brief_text(payload)
    if not isinstance(payload, dict):
        return _brief_text(json.dumps(payload, ensure_ascii=False, indent=1))

    out = Text(style="dim")
    scalars = [
        f"{key}={value}"
        for key, value in payload.items()
        if value is not None and not isinstance(value, (dict, list))
        and not (isinstance(value, str) and "\n" in value)
    ]
    if scalars:
        out.append("↳ " + _clip("  ".join(scalars), 200) + "\n")
    for key, value in payload.items():
        if isinstance(value, str) and "\n" in value:
            out.append(f"{key}:\n")
            out.append_text(_brief_text(value))
            out.append("\n")
        elif isinstance(value, list):
            items = ", ".join(_clip(json.dumps(item, ensure_ascii=False), 60) for item in value[:3])
            more = f" … (+{len(value) - 3})" if len(value) > 3 else ""
            out.append(f"{key}: {len(value)} item(s): {items}{more}\n")
        elif isinstance(value, dict):
            out.append(f"{key}: " + _clip(json.dumps(value, ensure_ascii=False), 200) + "\n")
    out.rstrip()
    return out


def show_user_message(text: str, source: str | None = None) -> None:
    console.print(
        Panel(Text(text.strip()), title="You" + (f" · {source}" if source else ""),
              title_align="left", border_style="cyan")
    )


class TurnView:
    """What one model call looks like while it streams: thinking, then writing."""

    def __init__(self) -> None:
        self.started = time.perf_counter()
        self.thinking = ""
        self.content = ""
        self.thinking_started: float | None = None
        self.thinking_ended: float | None = None

    def add(self, thinking: str | None, content: str | None) -> None:
        now = time.perf_counter()
        if thinking:
            self.thinking_started = self.thinking_started or now
            self.thinking += thinking
        if content and self.thinking_started and not self.thinking_ended:
            self.thinking_ended = now
        if content:
            self.content += content

    def finish(self) -> None:
        if self.thinking_started and not self.thinking_ended:
            self.thinking_ended = time.perf_counter()

    @property
    def thinking_s(self) -> float:
        if not self.thinking_started:
            return 0.0
        return (self.thinking_ended or time.perf_counter()) - self.thinking_started

    def __rich__(self) -> Group:
        parts: list[Any] = []
        if not self.thinking and not self.content:
            waited = duration(time.perf_counter() - self.started)
            parts.append(Text(f"  Reading the prompt… {waited}", style="dim"))
        if self.thinking:
            tail = "\n".join(self.thinking.strip()[-600:].splitlines()[-4:])
            parts.append(
                Panel(Text(tail, style="dim italic"),
                      title=f"Thinking · {duration(self.thinking_s)}", title_align="left",
                      border_style="grey50")
            )
        if self.content:
            tail = "\n".join(self.content.strip()[-1200:].splitlines()[-8:])
            parts.append(Panel(Text(tail), title="Assistant · writing…", title_align="left",
                               border_style="green"))
        return Group(*parts)


@contextmanager
def live_turn(enabled: bool) -> Iterator[TurnView]:
    """Show a model call live while it streams; erase it when done."""
    view = TurnView()
    if not enabled:
        yield view
        view.finish()
        return
    with Live(view, console=console, refresh_per_second=8, transient=True):
        yield view
    view.finish()


def show_thinking(view: TurnView, full: bool) -> None:
    """After a model call: the thinking, collapsed to one line or in full."""
    thinking = view.thinking.strip()
    if not thinking:
        return
    if full:
        console.print(
            Panel(Text(thinking, style="dim italic"), title=f"Thought for {duration(view.thinking_s)}",
                  title_align="left", border_style="grey50")
        )
        return
    first = thinking.replace("\n", " ").split(". ")[0].strip()
    console.print(
        Text(f"  Thought for {duration(view.thinking_s)} · \"{_clip(first, 120)}\"", style="dim italic")
    )
