"""Rich rendering. Useful for learning, not part of the logic."""

import json
from collections.abc import Sequence
from itertools import pairwise
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

console = Console(
    width=80,
)

ACTOR_STYLE = {
    "APP": "magenta",
    "EMBEDDING MODEL": "cyan",
    "GENERATIVE MODEL": "green",
    "MCP SERVER": "yellow",
}


def shorten_vectors(value: Any) -> Any:
    """Long lists of floats (embeddings) become 4 values and a count."""
    if isinstance(value, list):
        if len(value) > 8 and all(isinstance(x, float) for x in value):
            return [*value[:4], f"… {len(value) - 4} more floats ({len(value)} total)"]
        return [shorten_vectors(x) for x in value]
    if isinstance(value, dict):
        return {key: shorten_vectors(item) for key, item in value.items()}
    return value


def _json(value: Any) -> Syntax:
    text = json.dumps(shorten_vectors(value), ensure_ascii=False, indent=2, default=str)
    return Syntax(text, "json", word_wrap=True, padding=0)


def show_actors(rows: list[tuple[str, str]]) -> None:
    table = Table(title="Actors", expand=True)
    table.add_column("Actor")
    table.add_column("Meaning")
    for actor, meaning in rows:
        table.add_row(Text(actor, style=ACTOR_STYLE.get(actor, "")), meaning)
    console.print(table)


def show_http(actor: str, url: str, body: dict, response: dict) -> None:
    style = ACTOR_STYLE.get(actor, "white")
    title = f"APP -> {actor} · " + (f"POST {url}" if url.startswith("http") else url)
    console.print(Panel(_json(body), title=title, border_style=style))
    console.print(Panel(_json(response), title=f"{actor} -> APP", border_style=style))


def show_question(index: int, total: int, text: str) -> None:
    console.rule(f"[bold]QUESTION {index}/{total}")
    console.print(Panel(text, title="Question", border_style="white"))


def show_hits(hits: Sequence[Any], relevant: frozenset[str] = frozenset(), title: str = "Retrieved", show_text: bool = False) -> None:
    table = Table(title=title, expand=True)
    for column in ("rank", "chunk", "score", "relevant"):
        table.add_column(column)
    if show_text:
        table.add_column("text")
    for hit in hits:
        mark = "✓" if hit.chunk.section_id in relevant else ""
        row = [str(hit.rank), hit.chunk.id, f"{hit.score:.3f} ({hit.kind})", mark]
        if show_text:
            row.append(" ".join(hit.chunk.text.split())[:90])
        table.add_row(*row)
    console.print(table)


def show_context(context: Any, reason: str = "") -> None:
    if not context.chunks:
        console.print(Panel(f"empty context ({reason or 'no chunks'})", title="Context · APP", border_style="magenta"))
        return
    footer = f"{len(context.chunks)} chunks · ~{context.tokens} tokens (estimated)"
    if context.dropped:
        footer += f" · dropped by budget: {', '.join(c.id for c in context.dropped)}"
    console.print(Panel(Text(context.text), title="Context · what the APP gives the generator", subtitle=footer, border_style="magenta"))


def show_answer(trace: Any) -> None:
    if trace.abstained:
        console.print(Panel(f"{trace.answer}\n\nThe APP abstained ({trace.abstain_reason}); the generator was not called.",
                            title="Answer · APP", border_style="magenta"))
        return
    if trace.thinking:
        console.print(Panel(Text(trace.thinking, style="dim"), title="Thinking · GENERATIVE MODEL (--think)",
                            border_style="dim green"))
    status = "citations ok" if trace.citations.ok else f"citation problem: {trace.citations.problem}"
    subtitle = (f"{trace.model} · {trace.seconds_generation:.1f}s · prompt {trace.prompt_tokens} tokens "
                f"(est. context {trace.context.tokens}) · {status}")
    console.print(Panel(Text(trace.answer), title="Answer · GENERATIVE MODEL", subtitle=subtitle, border_style="green"))


def show_raw(text: str, title: str = "Rendered prompt · exactly what the generator reads") -> None:
    console.print(Panel(Text(text), title=title, border_style="green"))


def show_vector(label: str, vector: Any) -> None:
    import numpy as np

    values = ", ".join(f"{x:.3f}" for x in vector[:8])
    console.print(f"[cyan]{label}[/]  dim={len(vector)}  norm={float(np.linalg.norm(vector)):.4f}  [{values}, …]")


def show_table(title: str, columns: Sequence[str], rows: Sequence[Sequence[Any]]) -> None:
    table = Table(title=title, expand=True)
    for column in columns:
        table.add_column(str(column))
    for row in rows:
        table.add_row(*(f"{x:.3f}" if isinstance(x, float) else str(x) for x in row))
    console.print(table)


def show_histogram(groups: dict[str, list[float]], bins: list[float]) -> None:
    table = Table(title="Top-1 score per question", expand=True)
    table.add_column("score")
    for name in groups:
        table.add_column(name)
    for low, high in pairwise(bins):
        row = [f"{low:.2f}–{high:.2f}"]
        for scores in groups.values():
            count = sum(low <= s < high for s in scores)
            row.append("█" * count)
        table.add_row(*row)
    console.print(table)


def show_chunks(chunks: Sequence[Any], limit: int | None = None) -> None:
    table = Table(title=f"{len(chunks)} chunks", expand=True)
    for column in ("chunk", "words", "text"):
        table.add_column(column)
    for chunk in list(chunks)[:limit]:
        table.add_row(chunk.id, str(len(chunk.text.split())), " ".join(chunk.text.split())[:100])
    console.print(table)


def show_note(text: str) -> None:
    console.print(f"[dim]{text}[/]")


def show_error(text: str) -> None:
    console.print(Panel(text, title="Error", border_style="red"))


def show_todo(function: str, why: str) -> None:
    console.print(Panel(f"{function} is not implemented yet.\n{why}", title="TODO", border_style="yellow"))
