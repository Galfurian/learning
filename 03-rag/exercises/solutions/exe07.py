"""EXE07 — exact identifiers, two retrievers, one ranking. Task: see README.md."""

from raglab.corpus import Chunk
from raglab.embedders import tokens
from raglab.index import Hit
from raglab.runners import run_hybrid


def keyword_search(chunks: list[Chunk], weights: dict[str, float], query: str, k: int) -> list[Hit]:
    terms = set(tokens(query))
    scored = []
    for position, chunk in enumerate(chunks):
        present = terms & set(tokens(chunk.text))
        score = sum(weights.get(t, 0.0) for t in present)
        if score > 0:
            scored.append((score, position, chunk))
    scored.sort(key=lambda row: (-row[0], row[1]))
    return [Hit(chunk, score, rank, "keyword") for rank, (score, _, chunk) in enumerate(scored[:k], start=1)]


def fuse(rankings: list[list[Hit]], k: int = 60) -> list[Hit]:
    scores: dict[str, float] = {}
    chunks: dict[str, Chunk] = {}
    for ranking in rankings:
        for hit in ranking:
            scores[hit.chunk.id] = scores.get(hit.chunk.id, 0.0) + 1 / (k + hit.rank)
            chunks.setdefault(hit.chunk.id, hit.chunk)
    order = sorted(scores, key=lambda cid: -scores[cid])
    return [Hit(chunks[cid], scores[cid], rank, "rrf") for rank, cid in enumerate(order, start=1)]


if __name__ == "__main__":
    run_hybrid(keyword_search, fuse, __file__)
