"""Manuals in Markdown -> sections with stable ids.

Relevance labels point at section ids. Chunk ids change with the chunk size;
section ids do not.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from .cache import UNIT_ROOT

DATA_DIR = UNIT_ROOT / "data"
DEV_MANUALS = DATA_DIR / "dev" / "manuals"
DEV_QUESTIONS = DATA_DIR / "dev" / "questions.json"
PLANT_MANUALS = DATA_DIR / "plant" / "manuals"
PLANT_HOLDOUT = DATA_DIR / "plant" / "holdout.json"

HEADING = re.compile(r"^## (?P<title>.+?)\s*(?:\{#(?P<id>[a-z0-9-]+)\})?\s*$")


@dataclass(frozen=True)
class Section:
    id: str
    source: str
    title: str
    text: str


@dataclass(frozen=True)
class Chunk:
    id: str
    section_id: str
    source: str
    title: str
    text: str


def parse_manual(markdown: str, file: str) -> list[Section]:
    lines = markdown.splitlines()
    titles = [line[2:].strip() for line in lines if line.startswith("# ")]
    if not titles:
        raise ValueError(f"{file}: no '# ' title line")
    source = titles[0]
    sections: list[Section] = []
    current: tuple[str, str] | None = None
    body: list[str] = []

    def close() -> None:
        if current is not None:
            sections.append(Section(current[0], source, current[1], "\n".join(body).strip()))

    for number, line in enumerate(lines, start=1):
        if line.startswith("# "):
            continue
        if line.startswith("## "):
            match = HEADING.match(line)
            if not match or not match.group("id"):
                raise ValueError(f"{file}:{number}: section heading has no {{#id}}: {line!r}")
            close()
            if any(s.id == match.group("id") for s in sections):
                raise ValueError(f"{file}:{number}: duplicate section id '{match.group('id')}'")
            current = (match.group("id"), match.group("title"))
            body = []
        elif current is None:
            if line.strip():
                raise ValueError(f"{file}:{number}: text before the first section")
        else:
            body.append(line)
    close()
    return sections


def load_manuals(directory: Path) -> list[Section]:
    sections: list[Section] = []
    seen: set[str] = set()
    for path in sorted(Path(directory).glob("*.md")):
        for section in parse_manual(path.read_text(encoding="utf-8"), path.name):
            if section.id in seen:
                raise ValueError(f"{path.name}: duplicate section id '{section.id}'")
            seen.add(section.id)
            sections.append(section)
    if not sections:
        raise ValueError(f"no manuals in {directory}")
    return sections
