"""EXE05 — candidate depth. Task: see README.md in this folder."""

from collections.abc import Callable

from reranklab.evalset import Question
from reranklab.index import Hit
from reranklab.metrics import evidence_recall_at_k, mean_ndcg
from reranklab.runners import run_depth


# TODO: for every depth N in `depths`:
#   cut   = {id: candidates[id][:N]}                       the first stage's top N
#   after = {q.id: rerank_fn(q, cut[q.id]) for q in questions}
# and return one dict per depth:
#   {"depth": N,
#    "ceiling":        evidence_recall_at_k(questions, cut, N),
#    "first_stage@1":  evidence_recall_at_k(questions, cut, 1),
#    "reranked@1":     evidence_recall_at_k(questions, after, 1),
#    "nDCG@3":         mean_ndcg(questions, after, ideals, 3)}
def depth_curve(questions: list[Question], candidates: dict[str, list[Hit]],
                rerank_fn: Callable[[Question, list[Hit]], list[Hit]], depths: list[int],
                ideals: dict[str, list[int]]) -> list[dict]:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_depth(depth_curve, __file__)
