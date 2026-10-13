"""Copied from unit 04 (04-reranking/src/reranklab/ui.py), trimmed to what unit 05 uses."""

import json
from collections.abc import Sequence
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
    "RERANKER": "yellow",
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


def show_context(context: Any, title: str = "Context · what the APP gives the generator") -> None:
    if not context.ids:
        console.print(Panel("empty context: nothing found", title=title, border_style="magenta"))
        return
    footer = f"{len(context.ids)} items · ~{context.tokens} tokens (estimated)"
    if context.dropped:
        footer += f" · {context.dropped} dropped by the budget"
    console.print(Panel(Text(context.text), title=title, subtitle=footer, border_style="magenta"))


def show_answer(answer: Any, model: str) -> None:
    c, s = answer.citations, answer.score
    status = "citations ok" if c.ok else f"citation problem: {c.problem}"
    verdict = "right" if s.ok else ("refused" if s.refused else f"wrong (missing {s.missing}, extra {s.extra})")
    console.print(Panel(Text(answer.text), title="Answer · GENERATIVE MODEL", border_style="green",
                        subtitle=f"{model} · {answer.seconds:.1f}s · {status} · {verdict}"))


def show_plan(plan: Any, starts: Sequence[Any]) -> None:
    if plan is None:
        console.print(Panel("no plan: the planner did not recognize the question", title="Plan · APP",
                            border_style="magenta"))
        return
    linked = ", ".join(f"{r.mention!r} -> {r.node} ({r.level})" for r in starts) or "-"
    console.print(Panel(f"path   {' -> '.join(plan.path) or '-'}   op {plan.op}   rule {plan.why}\nstart  {linked}",
                        title="Plan · APP", border_style="magenta"))


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
