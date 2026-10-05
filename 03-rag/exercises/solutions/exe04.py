"""EXE04 — the index and the eval set. Task: see README.md in this folder."""

import numpy as np

from raglab.corpus import Chunk
from raglab.evalset import Question
from raglab.index import Hit
from raglab.runners import run_retrieval


def search(vectors: np.ndarray, chunks: list[Chunk], query: np.ndarray, k: int) -> list[Hit]:
    scores = vectors @ query
    order = np.argsort(-scores, kind="stable")[:k]
    return [Hit(chunks[i], float(scores[i]), rank) for rank, i in enumerate(order, start=1)]


def recall_at_k(questions: list[Question], results: dict[str, list[Hit]], k: int) -> float:
    answerable = [q for q in questions if q.relevant]
    if not answerable:
        raise ValueError("no answerable questions")
    found = sum(any(h.chunk.section_id in q.relevant for h in results[q.id][:k]) for q in answerable)
    return found / len(answerable)


if __name__ == "__main__":
    run_retrieval(search, recall_at_k, __file__)
