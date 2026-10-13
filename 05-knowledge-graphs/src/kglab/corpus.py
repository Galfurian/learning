"""Adapted from unit 04 (04-reranking/src/reranklab/corpus.py): the prose notes of the line.

One `##` section is one chunk, and its `{#id}` anchor is the chunk id. The
gold graph and the questions point at these ids, so they must not change
with a chunk size. The sections are short on purpose.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from .cache import UNIT_ROOT

DATA_DIR = UNIT_ROOT / "data"
LINE_DIR = DATA_DIR / "line"
MODELS_DIR = LINE_DIR / "models"
NOTES_DIR = LINE_DIR / "notes"
GOLD_GRAPH = DATA_DIR / "gold.json"
MANIFEST = DATA_DIR / "manifest.json"
DEV_QUESTIONS = DATA_DIR / "dev.json"
HOLDOUT_QUESTIONS = DATA_DIR / "holdout.json"

HEADING = re.compile(r"^## (?P<title>.+?)\s*(?:\{#(?P<id>[a-z0-9-]+)\})?\s*$")


@dataclass(frozen=True)
class Chunk:
    id: str
    section_id: str     # the same as id for a note; the model path for a data model chunk
    source: str         # the document title
    title: str
    text: str


def parse_note(markdown: str, file: str) -> list[Chunk]:
    lines = markdown.splitlines()
    titles = [line[2:].strip() for line in lines if line.startswith("# ")]
    if not titles:
        raise ValueError(f"{file}: no '# ' title line")
    source = titles[0]
    chunks: list[Chunk] = []
    current: tuple[str, str] | None = None
    body: list[str] = []

    def close() -> None:
        if current is not None:
            chunks.append(Chunk(current[0], current[0], source, current[1], "\n".join(body).strip()))

    for number, line in enumerate(lines, start=1):
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            match = HEADING.match(line)
            if not match or not match.group("id"):
                raise ValueError(f"{file}:{number}: section heading has no {{#id}}: {line!r}")
            close()
            if any(c.id == match.group("id") for c in chunks):
                raise ValueError(f"{file}:{number}: duplicate section id '{match.group('id')}'")
            current = (match.group("id"), match.group("title"))
            body = []
        elif current is None:
            if line.strip():
                raise ValueError(f"{file}:{number}: text before the first section")
        else:
            body.append(line)
    close()
    return chunks


def load_notes(directory: Path = NOTES_DIR) -> list[Chunk]:
    chunks: list[Chunk] = []
    seen: set[str] = set()
    for path in sorted(Path(directory).glob("*.md")):
        for chunk in parse_note(path.read_text(encoding="utf-8"), path.name):
            if chunk.id in seen:
                raise ValueError(f"{path.name}: duplicate section id '{chunk.id}'")
            seen.add(chunk.id)
            chunks.append(chunk)
    if not chunks:
        raise ValueError(f"no notes in {directory}")
    return chunks
