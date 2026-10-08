from reranklab.checks import run_checks
from reranklab.corpus import Chunk
from reranklab.evalset import Question
from reranklab.index import Hit

Q = Question("q", "x", frozenset({"m-errors"}), "code", "", ("E-1",))
EVIDENCE = Chunk("m-errors-2", "m-errors", "M", "T", "E-1: fan")
NOISE = [Chunk(f"n{i}-1", f"n{i}", "M", "T", "noise") for i in range(6)]


def perfect(question, hits):
    return sorted(hits, key=lambda h: h.chunk is not EVIDENCE)


def checks(exe, check):
    # The evidence chunk is the 7th first-stage candidate.
    hits = [Hit(c, 0.9 - i / 100, i + 1, first_rank=i + 1) for i, c in enumerate(NOISE + [EVIDENCE])]
    done, rows = check.calls(exe.depth_curve, [Q], {"q": hits}, perfect, [5, 10], {"q": [2]})
    if not done:
        return
    check.ok([r["depth"] for r in rows] == [5, 10], "one row per depth, in order", rows)
    five, ten = rows
    check.ok(five["ceiling"] == 0.0 and ten["ceiling"] == 1.0, "ceiling: is the evidence among the first N?", rows)
    check.ok(five["reranked@1"] == 0.0, "depth 5: even a perfect reranker cannot reach it", five)
    check.ok(ten["reranked@1"] == 1.0 and ten["first_stage@1"] == 0.0, "depth 10: the reranker moves it to rank 1", ten)
    check.ok(abs(ten["nDCG@3"] - 1.0) < 1e-9, "nDCG@3 after reranking at depth 10", ten["nDCG@3"])


run_checks(checks, __file__.replace("check.py", "exe05.py"))
