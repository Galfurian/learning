"""EXE05 — candidate depth. Task: see README.md in this folder."""

from collections.abc import Callable

from reranklab.evalset import Question
from reranklab.index import Hit
from reranklab.metrics import evidence_recall_at_k, mean_ndcg
from reranklab.runners import run_depth


def depth_curve(questions: list[Question], candidates: dict[str, list[Hit]],
                rerank_fn: Callable[[Question, list[Hit]], list[Hit]], depths: list[int],
                ideals: dict[str, list[int]]) -> list[dict]:
    rows = []
    for n in depths:
        cut = {qid: hits[:n] for qid, hits in candidates.items()}
        after = {q.id: rerank_fn(q, cut[q.id]) for q in questions}
        rows.append({
            "depth": n,
            "ceiling": evidence_recall_at_k(questions, cut, n),
            "first_stage@1": evidence_recall_at_k(questions, cut, 1),
            "reranked@1": evidence_recall_at_k(questions, after, 1),
            "nDCG@3": mean_ndcg(questions, after, ideals, 3),
        })
    return rows


if __name__ == "__main__":
    run_depth(depth_curve, __file__)
