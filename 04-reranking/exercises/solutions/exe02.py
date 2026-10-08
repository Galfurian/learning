"""EXE02 — graded relevance and nDCG. Task: see README.md in this folder."""

import math

from reranklab.corpus import Chunk
from reranklab.evalset import Question
from reranklab.runners import run_ndcg


def gain(chunk: Chunk, question: Question) -> int:
    if chunk.section_id not in question.relevant:
        return 0
    text = chunk.text.lower()
    return 2 if all(m.lower() in text for m in question.must_contain) else 1


def ndcg_at_k(gains: list[int], ideal: list[int], k: int) -> float:
    def dcg(values: list[int]) -> float:
        return sum((2**g - 1) / math.log2(i + 1) for i, g in enumerate(values[:k], start=1))

    best = dcg(ideal)
    return dcg(gains) / best if best else 0.0


if __name__ == "__main__":
    run_ndcg(gain, ndcg_at_k, __file__)
