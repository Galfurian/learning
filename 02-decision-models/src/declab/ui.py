"""Rich rendering for the observation modes. Not part of the decision logic."""

import json
from typing import Any

from rich.console import Console, Group
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

console = Console()

BAR_WIDTH = 24


def _json(value: Any) -> Syntax:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    return Syntax(text, "json", word_wrap=True, padding=0)


def _state_view(state: Any) -> Any:
    return Text(state) if isinstance(state, str) else _json(state)


def _bar(probability: float) -> Text:
    filled = round(probability * BAR_WIDTH)
    text = Text("█" * filled, style="green")
    text.append("░" * (BAR_WIDTH - filled), style="dim")
    text.append(f" {probability:.3f}")
    return text


def _short(value: Any, width: int = 48) -> str:
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    text = " ".join(text.split())
    return text if len(text) <= width else text[: width - 1] + "…"


def show_actors(model: str, file_label: str) -> None:
    table = Table(title="Actors", show_header=True, header_style="bold", expand=True)
    table.add_column("Actor")
    table.add_column("Meaning")
    table.add_row(
        "APP",
        f"{file_label}: ordinary Python. Builds the state, asks the questions, "
        "and runs act() on the answers. Only the APP does things.",
    )
    table.add_row(
        "OLLAMA",
        f"Local runtime at /v1/systemone running {model}. Reads state + questions "
        "and returns probabilities. It never acts.",
    )
    console.print(table)


def show_case_header(index: int, total: int) -> None:
    console.rule(f"[bold]CASE {index}/{total}")


def show_state(state: Any) -> None:
    console.print(Panel(_state_view(state), title="State · what the model reads", border_style="cyan"))


def show_request(body: dict[str, Any]) -> None:
    console.print(Panel(_json(body), title="APP -> OLLAMA · POST /v1/systemone", border_style="blue"))


def show_response(raw: dict[str, Any]) -> None:
    console.print(Panel(_json(raw), title="OLLAMA -> APP · response", border_style="blue"))


def _answer_rows(name: str, answer: dict[str, Any]) -> list[Any]:
    kind = answer.get("type")
    rows: list[Any] = []
    if kind == "noul":
        line = Text(f"{name}", style="bold")
        line.append("  noul  P(true) ")
        line.append_text(_bar(answer.get("noul", 0.0)))
        rows.append(line)
    elif kind == "choice":
        line = Text(f"{name}", style="bold")
        line.append(f"  choice -> {answer.get('choice')}", style="bold green")
        line.append(f"   confidence {answer.get('confidence', 0):.3f}", style="dim")
        rows.append(line)
        probabilities = answer.get("probabilities", {})
        for option, p in sorted(probabilities.items(), key=lambda item: -item[1]):
            option_line = Text(f"    {option:<22}")
            option_line.append_text(_bar(p))
            rows.append(option_line)
    elif kind == "score":
        legend = answer.get("legend", {})
        score = answer.get("score", 0.0)
        nearest = legend.get(str(round(score)), "")
        line = Text(f"{name}", style="bold")
        line.append(f"  score {score:.2f}", style="bold green")
        line.append(f" (nearest: {nearest})")
        line.append(f"   confidence {answer.get('confidence', 0):.3f}", style="dim")
        rows.append(line)
        for index, p in answer.get("probabilities", {}).items():
            option_line = Text(f"    {index} {legend.get(index, ''):<20}")
            option_line.append_text(_bar(p))
            rows.append(option_line)
    else:
        rows.append(Text(f"{name}  {answer}"))
    return rows


def show_decision(
    answers: dict[str, Any],
    model: str,
    seconds: float,
    usage: dict[str, int],
    requests: int = 1,
) -> None:
    rows: list[Any] = []
    for name, answer in answers.items():
        rows += _answer_rows(name, answer)
    rows.append(Text())
    rows.append(
        Text(
            f"{requests} request(s) · {usage.get('input_tokens', 0)} input tokens · "
            f"{usage.get('output_tokens', 0)} output tokens · {seconds:.2f}s",
            style="dim",
        )
    )
    console.print(
        Panel(Group(*rows), title=f"Decision · the MODEL answered ({model})", border_style="green")
    )


def show_action(action: Any) -> None:
    console.print(
        Panel(Text(str(action), style="bold"), title="Action · your APP code acted (act)", border_style="magenta")
    )


def show_todo(function: str, detail: str = "") -> None:
    text = Text(f"{function} is not implemented yet.", style="bold yellow")
    if detail:
        text.append(f"\n{detail}", style="yellow")
    console.print(Panel(text, title="TODO", border_style="yellow"))


def show_note(message: str) -> None:
    console.print(f"[dim]{message}[/dim]")


def show_error(message: str) -> None:
    console.print(Panel(Text(message, style="bold red"), title="OLLAMA -> APP · error", border_style="red"))


def show_problems(found: list[str]) -> None:
    if not found:
        console.print("[green]local validation: the request is well formed[/green]")
        return
    console.print("[red]local validation: Ollama would reject this request[/red]")
    for problem in found:
        console.print(f"[red]  - {problem}[/red]")


def show_summary(rows: list[tuple[str, str, str, float]], total_s: float, tokens: int) -> None:
    table = Table(title="Summary", show_header=True, header_style="bold", expand=True)
    table.add_column("#", justify="right")
    table.add_column("State")
    table.add_column("Decision (model)")
    table.add_column("Action (app)")
    table.add_column("s", justify="right")
    for index, (state, decision, action, seconds) in enumerate(rows, start=1):
        table.add_row(str(index), state, decision, action, f"{seconds:.1f}")
    console.print(table)
    console.print(f"[dim]{len(rows)} case(s) · {tokens} input tokens · {total_s:.1f}s total[/dim]")


def short_state(state: Any) -> str:
    return _short(state)


def short_decision(answers: dict[str, Any]) -> str:
    parts = []
    for name, answer in answers.items():
        kind = answer.get("type")
        if kind == "noul":
            parts.append(f"{name} p={answer.get('noul', 0):.2f}")
        elif kind == "choice":
            choice = answer.get("choice")
            p = answer.get("probabilities", {}).get(choice, 0)
            parts.append(f"{name}={choice} p={p:.2f}")
        elif kind == "score":
            parts.append(f"{name}={answer.get('score', 0):.2f}")
    return ", ".join(parts)
