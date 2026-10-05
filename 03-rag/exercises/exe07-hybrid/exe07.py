"""EXE07 — exact identifiers, two retrievers, one ranking. Task: see README.md."""

from raglab.corpus import Chunk
from raglab.embedders import tokens
from raglab.index import Hit
from raglab.runners import run_hybrid


# TODO: a keyword retriever. For each chunk, the score is the sum of
# weights[t] for every DISTINCT query token t (tokens(query)) that also
# appears in tokens(chunk.text). Return the k best chunks with a score > 0
# as Hit(chunk, score, rank, "keyword"), rank from 1, best first; on equal
# scores keep the chunk order.
def keyword_search(chunks: list[Chunk], weights: dict[str, float], query: str, k: int) -> list[Hit]:
    raise NotImplementedError("You need to implement this function.")


# TODO: reciprocal rank fusion. Every hit adds 1 / (k + hit.rank) to the
# score of its chunk (by chunk.id), over all rankings. Return one Hit per
# chunk, best first, as Hit(chunk, fused_score, rank, "rrf"); on equal scores
# keep the order of first appearance.
def fuse(rankings: list[list[Hit]], k: int = 60) -> list[Hit]:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_hybrid(keyword_search, fuse, __file__)
