"""EXE03 — chunking. Task: see README.md in this folder."""

from raglab.corpus import Chunk, Section
from raglab.runners import run_chunking

# Put "<manual> — <section title>" on the first line of every chunk?
WITH_TITLE = True


# TODO: split section.text into windows of `size` words. Each window starts
# `size - overlap` words after the previous one, and the last window ends at
# the last word. Return one Chunk per window:
#   id          f"{section.id}-{n}", n from 1
#   section_id  section.id
#   source, title  copied from the section
#   text        the words joined by spaces; when WITH_TITLE, prefixed by
#               f"{section.source} — {section.title}\n"
# An empty section gives []. Raise ValueError when size < 1 or when overlap
# is not between 0 and size - 1. Do not import raglab.chunking.
def chunk_section(section: Section, size: int, overlap: int) -> list[Chunk]:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_chunking(chunk_section, __file__)
