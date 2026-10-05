from raglab.checks import fake_chunk, run_checks
from raglab.context import estimate_tokens, format_chunk
from raglab.index import Hit


def checks(exe, check):
    a, b, c = fake_chunk("a-1", "x" * 40), fake_chunk("b-1", "y" * 40), fake_chunk("c-1", "z" * 4000)
    hits = [Hit(b, 0.8, 2), Hit(a, 0.9, 1), Hit(a, 0.9, 1), Hit(c, 0.7, 3)]
    one = estimate_tokens(format_chunk(a)) + 1
    done, context = check.calls(exe.build_context, hits, one * 2)
    if not done:
        return
    check.ok(context.ids == ["a-1", "b-1"], "rank order, each chunk once", context.ids)
    check.ok([x.id for x in context.dropped] == ["c-1"], "a chunk that does not fit is dropped", context.dropped)
    check.ok(context.text.startswith("[a-1]\n") and "\n\n[b-1]\n" in context.text, "chunks formatted with their [id]")
    check.ok(context.tokens <= one * 2, "the context fits the budget", context.tokens)
    small = fake_chunk("d-1", "short")
    skipped = exe.build_context([Hit(c, 0.9, 1), Hit(small, 0.8, 2)], 50)
    check.ok(skipped.ids == ["d-1"], "a big first chunk is skipped, the next one still fits", skipped.ids)
    check.ok(isinstance(exe.THRESHOLD, float) and 0.0 < exe.THRESHOLD < 1.0, "THRESHOLD is set between 0 and 1", exe.THRESHOLD)
    done, empty = check.calls(exe.answerable, [])
    if not done:
        return
    check.ok(empty is False, "no hits: not answerable")
    check.ok(exe.answerable([Hit(a, exe.THRESHOLD, 1)]), "a best score equal to THRESHOLD is answerable")
    check.ok(not exe.answerable([Hit(a, exe.THRESHOLD - 0.01, 1)]), "below THRESHOLD: abstain")


run_checks(checks, __file__.replace("check.py", "exe05.py"))
