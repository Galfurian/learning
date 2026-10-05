import numpy as np

from raglab.checks import run_checks
from raglab.embedders import FakeEmbedder


def checks(exe, check):
    check.ok(len(exe.PAIRS) >= 10, "PAIRS has your two extra pairs", len(exe.PAIRS))
    check.ok(all(p[2] in ("same", "different") for p in exe.PAIRS), "every pair is labeled 'same' or 'different'")
    done, out = check.calls(exe.normalize, np.array([3.0, 4.0]))
    if not done:
        return
    check.ok(np.allclose(out, [0.6, 0.8]), "normalize([3, 4]) == [0.6, 0.8]", out)
    original = np.array([0.0, 2.0])
    exe.normalize(original)
    check.ok(np.allclose(original, [0.0, 2.0]), "normalize() does not modify its input")
    zero = exe.normalize(np.zeros(3))
    check.ok(not np.isnan(zero).any() and np.allclose(zero, 0), "a zero vector stays zero (no division by 0)", zero)
    raw = FakeEmbedder(dim=64, normalized=False).embed_query("belt tension belt squeal")
    check.ok(abs(np.linalg.norm(exe.normalize(raw)) - 1) < 1e-6, "a FakeEmbedder vector has length 1 after normalize()")


run_checks(checks, __file__.replace("check.py", "exe01.py"))
