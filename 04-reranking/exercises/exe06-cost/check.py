from reranklab.checks import run_checks

ROWS = [
    {"config": "none", "evidence_recall@1": 0.6, "nDCG@3": 0.6, "s/question": 0.0},
    {"config": "minilm-20", "evidence_recall@1": 0.9, "nDCG@3": 0.8, "s/question": 0.7},
    {"config": "minilm-20-copy", "evidence_recall@1": 0.9, "nDCG@3": 0.8, "s/question": 0.9},
    {"config": "minilm-50", "evidence_recall@1": 0.9, "nDCG@3": 0.85, "s/question": 1.6},
    {"config": "tev1-20", "evidence_recall@1": 0.95, "nDCG@3": 0.9, "s/question": 40.0},
]


def checks(exe, check):
    done, pick = check.calls(exe.pick_config, ROWS, 1.0)
    if not done:
        return
    check.ok(pick and pick["config"] == "minilm-20", "within 1 s: best recall, then the cheaper of equal rows", pick)
    check.ok(exe.pick_config(ROWS, 2.0)["config"] == "minilm-50", "within 2 s: same recall, better nDCG@3")
    check.ok(exe.pick_config(ROWS, 100)["config"] == "tev1-20", "a large budget buys the best quality")
    check.ok(exe.pick_config(ROWS, 0.0)["config"] == "none", "budget 0: only no reranker fits")
    check.ok(exe.pick_config(ROWS, -1) is None, "nothing fits: None")


run_checks(checks, __file__.replace("check.py", "exe06.py"))
