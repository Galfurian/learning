"""EXE02 — rank chunks by similarity. Task: see README.md in this folder."""

import numpy as np

from raglab.runners import run_ranking


# TODO: the cosine of the angle between a and b: dot(a, b) / (|a| * |b|).
# Return 0.0 when one of the two vectors is zero.
def cosine(a: np.ndarray, b: np.ndarray) -> float:
    raise NotImplementedError("You need to implement this function.")


# TODO: score every row of `vectors` against `query` with cosine(), and
# return the k best as (id, score) pairs, best first. On equal scores, keep
# the original order of `ids`.
def top_k(query: np.ndarray, vectors: np.ndarray, ids: list[str], k: int) -> list[tuple[str, float]]:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_ranking(cosine, top_k, __file__)
