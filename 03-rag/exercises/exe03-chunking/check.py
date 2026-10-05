from raglab.checks import fake_section, run_checks


def body(chunk, with_title):
    return chunk.text.split("\n", 1)[1] if with_title else chunk.text


def checks(exe, check):
    section = fake_section("demo-errors", " ".join(f"w{i}" for i in range(1, 11)), title="Error codes")
    done, chunks = check.calls(exe.chunk_section, section, 4, 1)
    if not done:
        return
    words = [body(c, exe.WITH_TITLE).split() for c in chunks]
    check.ok([c.id for c in chunks] == ["demo-errors-1", "demo-errors-2", "demo-errors-3"],
             "10 words, size 4, overlap 1 -> ids demo-errors-1..3", [c.id for c in chunks])
    check.ok(words[:2] == [["w1", "w2", "w3", "w4"], ["w4", "w5", "w6", "w7"]], "windows overlap by 1 word", words)
    check.ok(words and words[-1][-1] == "w10", "the last chunk ends at the last word")
    check.ok(all(len(w) <= 4 for w in words), "no chunk has more than `size` words (title line excluded)")
    check.ok(all(c.section_id == "demo-errors" and c.title == "Error codes" for c in chunks), "chunks keep section_id and title")
    if exe.WITH_TITLE:
        check.ok(chunks[1].text.startswith("Demo machine — Error codes\n"), "every chunk starts with the title line")
    check.ok(len(exe.chunk_section(fake_section("s", "only three words"), 60, 15)) == 1, "a short section is one chunk")
    check.ok(exe.chunk_section(fake_section("s", ""), 60, 15) == [], "an empty section gives no chunks")
    for size, overlap in [(4, 4), (0, 0), (4, -1)]:
        try:
            exe.chunk_section(section, size, overlap)
            check.ok(False, f"size={size}, overlap={overlap} raises ValueError")
        except ValueError:
            check.ok(True, f"size={size}, overlap={overlap} raises ValueError")


run_checks(checks, __file__.replace("check.py", "exe03.py"))
