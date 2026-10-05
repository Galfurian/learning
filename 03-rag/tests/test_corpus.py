import json

import pytest

from raglab.chunking import chunk_all, chunk_section, windows
from raglab.corpus import (
    DEV_MANUALS,
    DEV_QUESTIONS,
    Section,
    load_manuals,
    parse_manual,
)

MANUAL = """# Demo machine

## First part {#demo-first}

One two three.

Four five.

## Second part {#demo-second}

Six.
"""


def test_parse_manual():
    sections = parse_manual(MANUAL, "demo.md")
    assert [s.id for s in sections] == ["demo-first", "demo-second"]
    assert sections[0] == Section("demo-first", "Demo machine", "First part", "One two three.\n\nFour five.")


@pytest.mark.parametrize(
    "text, message",
    [
        ("## A {#a}\n\nx\n", "no '# ' title"),
        ("# T\n\nloose text\n## A {#a}\nx\n", "text before the first section"),
        ("# T\n## A\nx\n", "has no {#id}"),
        ("# T\n## A {#a}\nx\n## B {#a}\ny\n", "duplicate section id 'a'"),
    ],
)
def test_parse_manual_errors(text, message):
    with pytest.raises(ValueError, match=message):
        parse_manual(text, "bad.md")


def test_windows():
    words = list("abcdefg")
    assert windows(words, 3, 1) == [list("abc"), list("cde"), list("efg")]
    assert windows(words, 10, 2) == [words]
    assert windows([], 3, 0) == []
    with pytest.raises(ValueError):
        windows(words, 3, 3)
    with pytest.raises(ValueError):
        windows(words, 0, 0)


def test_chunk_section_ids_and_title():
    section = Section("demo-first", "Demo machine", "First part", "one two three four five")
    chunks = chunk_section(section, size=3, overlap=1)
    assert [c.id for c in chunks] == ["demo-first-1", "demo-first-2"]
    assert chunks[0].text == "Demo machine — First part\none two three"
    assert chunk_section(section, size=3, overlap=1, with_title=False)[0].text == "one two three"


def test_dev_corpus_is_consistent():
    sections = load_manuals(DEV_MANUALS)
    ids = {s.id for s in sections}
    assert len(sections) == 35
    questions = json.loads(DEV_QUESTIONS.read_text())
    assert len(questions) == 26
    for q in questions:
        assert set(q["relevant"]) <= ids, q["id"]
        text = " ".join(s.text for s in sections if s.id in q["relevant"]).lower()
        for needle in q["must_contain"]:
            assert needle.lower() in text, (q["id"], needle)
    assert len(chunk_all(sections)) >= 35
