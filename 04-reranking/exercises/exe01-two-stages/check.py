from reranklab.checks import fake_chunk, run_checks
from reranklab.index import Hit


def hits(n):
    return [Hit(fake_chunk(f"c{i}-1"), 1.0 - i / 10, i, first_rank=i) for i in range(1, n + 1)]


def fixed(values):
    return lambda question, passages: values[: len(passages)]


def checks(exe, check):
    done, out = check.calls(exe.rerank, "q", hits(4), fixed([0.1, 0.9, 0.5, 0.9]), 3)
    if not done:
        return
    ids = [h.chunk.id for h in out]
    check.ok(ids == ["c2-1", "c4-1", "c3-1"], "highest score first; equal scores keep the first-stage order", ids)
    check.ok([h.rank for h in out] == [1, 2, 3], "new ranks from 1", [h.rank for h in out])
    check.ok([h.first_rank for h in out] == [2, 4, 3], "every hit keeps its first-stage rank", [h.first_rank for h in out])
    check.ok(out[0].rerank_score == 0.9 and out[0].kind == "rerank", "rerank_score and kind are set", out[0])
    check.ok(len(exe.rerank("q", hits(2), fixed([0.5, 0.1]), 10)) == 2, "k larger than the candidates: nothing is added")
    check.ok(exe.rerank("q", [], fixed([]), 3) == [], "no candidates: nothing to rerank")
    without = [Hit(fake_chunk("x-1"), 0.5, 7)]
    check.ok(exe.rerank("q", without, fixed([1.0]), 1)[0].first_rank == 7, "first_rank falls back to rank")


run_checks(checks, __file__.replace("check.py", "exe01.py"))
