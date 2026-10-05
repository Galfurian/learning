"""EXE02 — rank chunks by similarity. Task: see README.md in this folder."""

import numpy as np

from raglab.runners import run_ranking


def cosine(a: np.ndarray, b: np.ndarray) -> float:
    norms = float(np.linalg.norm(a) * np.linalg.norm(b))
    if norms == 0.0:
        return 0.0
    return float(a @ b) / norms


def top_k(query: np.ndarray, vectors: np.ndarray, ids: list[str], k: int) -> list[tuple[str, float]]:
    scored = [(cid, cosine(query, row)) for cid, row in zip(ids, vectors)]
    scored.sort(key=lambda pair: pair[1], reverse=True)  # sort is stable: ties keep their order
    return scored[:k]


if __name__ == "__main__":
    run_ranking(cosine, top_k, __file__)
