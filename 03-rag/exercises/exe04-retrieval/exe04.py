"""EXE04 — the index and the eval set. Task: see README.md in this folder."""

import numpy as np

from raglab.corpus import Chunk
from raglab.evalset import Question
from raglab.index import Hit
from raglab.runners import run_retrieval


# TODO: `vectors` has one unit-length row per chunk, and `query` has unit
# length too. Score all rows with ONE matrix-vector product, then return the
# k best as Hit(chunk, score, rank), rank from 1, best first (ties keep the
# chunk order: use np.argsort(..., kind="stable") on the negated scores).
def search(vectors: np.ndarray, chunks: list[Chunk], query: np.ndarray, k: int) -> list[Hit]:
    raise NotImplementedError("You need to implement this function.")


# TODO: the fraction of ANSWERABLE questions (question.relevant is not empty)
# with at least one hit from a relevant section (hit.chunk.section_id in
# question.relevant) among the first k hits of results[question.id].
# Raise ValueError when there is no answerable question.
def recall_at_k(questions: list[Question], results: dict[str, list[Hit]], k: int) -> float:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_retrieval(search, recall_at_k, __file__)
