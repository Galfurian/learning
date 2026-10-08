"""EXE06 — cost versus quality. Task: see README.md in this folder."""

from reranklab.runners import run_cost


def pick_config(rows: list[dict], budget_s: float) -> dict | None:
    fits = [r for r in rows if r["s/question"] <= budget_s]
    if not fits:
        return None
    return max(fits, key=lambda r: (r["evidence_recall@1"], r["nDCG@3"], -r["s/question"]))


if __name__ == "__main__":
    run_cost(pick_config, __file__)
