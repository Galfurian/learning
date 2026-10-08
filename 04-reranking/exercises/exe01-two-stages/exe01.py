"""EXE01 — two stages: retrieve, then rerank. Task: see README.md in this folder."""

from collections.abc import Callable
from dataclasses import replace

from reranklab.index import Hit
from reranklab.runners import run_two_stages


# TODO: rerank the first stage's hits.
# - scores = score(question, [hit.chunk.text for hit in hits]): one relevance score per hit;
# - sort the hits by score, highest first; on equal scores keep the first-stage order;
# - keep the first k;
# - return new Hits with dataclasses.replace(hit, rank=<new rank from 1>, kind="rerank",
#   rerank_score=<its score>, first_rank=<hit.first_rank, or hit.rank if that is None>).
# Never add a hit that is not in `hits`.
def rerank(question: str, hits: list[Hit], score: Callable[[str, list[str]], list[float]], k: int) -> list[Hit]:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_two_stages(rerank, __file__)
