import numpy as np

from raglab.checks import run_checks


def checks(exe, check):
    done, value = check.calls(exe.cosine, np.array([1.0, 0.0]), np.array([0.0, 1.0]))
    if not done:
        return
    check.ok(abs(value) < 1e-9, "orthogonal vectors: cosine 0", value)
    check.ok(abs(exe.cosine(np.array([2.0, 0.0]), np.array([5.0, 0.0])) - 1) < 1e-9, "same direction, any length: cosine 1")
    check.ok(abs(exe.cosine(np.array([1.0, 1.0]), np.array([-1.0, -1.0])) + 1) < 1e-9, "opposite: cosine -1")
    check.ok(exe.cosine(np.zeros(2), np.array([1.0, 0.0])) == 0.0, "a zero vector gives 0.0, not nan")
    vectors = np.array([[0.0, 1.0], [1.0, 0.0], [1.0, 1.0], [1.0, 0.0]])
    done, ranked = check.calls(exe.top_k, np.array([1.0, 0.0]), vectors, ["a", "b", "c", "d"], 3)
    if not done:
        return
    check.ok([cid for cid, _ in ranked] == ["b", "d", "c"], "best first; equal scores keep their order", ranked)
    check.ok(all(isinstance(s, float) for _, s in ranked), "scores are floats")
    check.ok(len(exe.top_k(np.array([1.0, 0.0]), vectors, ["a", "b", "c", "d"], 10)) == 4, "k larger than the corpus returns all")


run_checks(checks, __file__.replace("check.py", "exe02.py"))
