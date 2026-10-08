import math

from reranklab.checks import run_checks
from reranklab.corpus import Chunk
from reranklab.evalset import Question

Q = Question("q", "x", frozenset({"m-errors"}), "code", "", ("E-1", "fan"))


def checks(exe, check):
    evidence = Chunk("m-errors-2", "m-errors", "M", "T", "E-1: the FAN stopped")
    half = Chunk("m-errors-1", "m-errors", "M", "T", "E-1: door")
    other = Chunk("m-parts-1", "m-parts", "M", "T", "E-1 fan")
    done, g = check.calls(exe.gain, evidence, Q)
    if not done:
        return
    check.ok(g == 2, "every fact, right section: gain 2 (case-insensitive)", g)
    check.ok(exe.gain(half, Q) == 1, "right section, missing facts: gain 1")
    check.ok(exe.gain(other, Q) == 0, "facts in the wrong section: gain 0")
    done, value = check.calls(exe.ndcg_at_k, [2, 1, 0], [2, 1], 3)
    if not done:
        return
    check.ok(abs(value - 1.0) < 1e-9, "ideal order: nDCG 1.0", value)
    expected = (1 + 3 / math.log2(3)) / (3 + 1 / math.log2(3))
    check.ok(abs(exe.ndcg_at_k([1, 2, 0], [2, 1], 3) - expected) < 1e-9, "swapped order: lower nDCG", exe.ndcg_at_k([1, 2, 0], [2, 1], 3))
    check.ok(exe.ndcg_at_k([0, 0, 2], [2], 1) == 0.0, "k cuts the list: evidence at rank 3 counts nothing at k = 1")
    check.ok(exe.ndcg_at_k([0], [], 3) == 0.0, "no relevant chunk anywhere: 0.0, not a division by zero")


run_checks(checks, __file__.replace("check.py", "exe02.py"))
