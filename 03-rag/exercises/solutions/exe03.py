"""EXE03 — chunking. Task: see README.md in this folder."""

from raglab.corpus import Chunk, Section
from raglab.runners import run_chunking

# Put "<manual> — <section title>" on the first line of every chunk?
WITH_TITLE = True


def chunk_section(section: Section, size: int, overlap: int) -> list[Chunk]:
    if size < 1 or not 0 <= overlap < size:
        raise ValueError("need size >= 1 and 0 <= overlap < size")
    words = section.text.split()
    header = f"{section.source} — {section.title}\n" if WITH_TITLE else ""
    chunks = []
    start = 0
    while start < len(words):
        part = words[start : start + size]
        chunks.append(Chunk(f"{section.id}-{len(chunks) + 1}", section.id, section.source, section.title,
                            header + " ".join(part)))
        if start + size >= len(words):
            break
        start += size - overlap
    return chunks


if __name__ == "__main__":
    run_chunking(chunk_section, __file__)
