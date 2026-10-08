"""EXE01 — two stages: retrieve, then rerank. Task: see README.md in this folder."""

from collections.abc import Callable
from dataclasses import replace

from reranklab.index import Hit
from reranklab.runners import run_two_stages


def rerank(question: str, hits: list[Hit], score: Callable[[str, list[str]], list[float]], k: int) -> list[Hit]:
    scores = score(question, [h.chunk.text for h in hits])
    order = sorted(range(len(hits)), key=lambda i: -scores[i])  # sorted() is stable
    return [
        replace(hits[i], rank=rank, kind="rerank", rerank_score=float(scores[i]),
                first_rank=hits[i].first_rank if hits[i].first_rank is not None else hits[i].rank)
        for rank, i in enumerate(order[:k], start=1)
    ]


if __name__ == "__main__":
    run_two_stages(rerank, __file__)
