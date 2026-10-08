"""EXE06 — cost versus quality. Task: see README.md in this folder."""

from reranklab.runners import run_cost


# TODO: choose the configuration to deploy under a CPU time budget.
# Each row: {"config": str, "evidence_recall@1": float, "nDCG@3": float, "s/question": float}.
# Keep only rows with s/question <= budget_s. Among them, take the highest
# evidence_recall@1; on a tie, the highest nDCG@3; on a tie again, the cheapest.
# Return None when no row fits.
def pick_config(rows: list[dict], budget_s: float) -> dict | None:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_cost(pick_config, __file__)
