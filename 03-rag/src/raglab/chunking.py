"""Sections -> chunks: windows of words, with the section title in front.

EXE03 writes its own ``chunk_section``. The later exercises use this one.
"""

from collections.abc import Callable, Sequence

from .corpus import Chunk, Section

DEFAULT_SIZE = 60
DEFAULT_OVERLAP = 15

Chunker = Callable[[Section, int, int], list[Chunk]]


def windows(words: list[str], size: int, overlap: int) -> list[list[str]]:
    if size < 1:
        raise ValueError("size must be at least 1")
    if not 0 <= overlap < size:
        raise ValueError("overlap must be between 0 and size - 1")
    if not words:
        return []
    step = size - overlap
    out = []
    start = 0
    while True:
        out.append(words[start : start + size])
        if start + size >= len(words):
            return out
        start += step


def chunk_section(
    section: Section,
    size: int = DEFAULT_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    with_title: bool = True,
) -> list[Chunk]:
    header = f"{section.source} — {section.title}\n" if with_title else ""
    return [
        Chunk(f"{section.id}-{n}", section.id, section.source, section.title, header + " ".join(part))
        for n, part in enumerate(windows(section.text.split(), size, overlap), start=1)
    ]


def chunk_all(
    sections: Sequence[Section],
    size: int = DEFAULT_SIZE,
    overlap: int = DEFAULT_OVERLAP,
    with_title: bool = True,
    chunker: Chunker | None = None,
) -> list[Chunk]:
    chunks: list[Chunk] = []
    for section in sections:
        if chunker is not None:
            chunks.extend(chunker(section, size, overlap))
        else:
            chunks.extend(chunk_section(section, size, overlap, with_title))
    return chunks
