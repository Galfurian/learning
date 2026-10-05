"""Keyword search (BM25) and rank fusion.

Semantic search matches meaning; keyword search matches exact tokens.
Identifiers such as PN-X7Q-919-A are one token for BM25, and just another
string of letters for an embedding model.
"""

import math
from collections import Counter
from collections.abc import Sequence

from .corpus import Chunk
from .embedders import tokens
from .index import Hit, Index


def idf(chunks: Sequence[Chunk]) -> dict[str, float]:
    df = Counter(t for c in chunks for t in set(tokens(c.text)))
    n = len(chunks)
    return {t: math.log(1 + n / count) for t, count in df.items()}


class BM25:
    def __init__(self, chunks: Sequence[Chunk], k1: float = 1.2, b: float = 0.75) -> None:
        self.chunks = list(chunks)
        self.k1, self.b = k1, b
        self.counts = [Counter(tokens(c.text)) for c in self.chunks]
        self.lengths = [sum(c.values()) for c in self.counts]
        self.average = sum(self.lengths) / len(self.lengths) if self.lengths else 0.0
        self.weights = idf(self.chunks)

    def search(self, query: str, k: int = 3) -> list[Hit]:
        terms = set(tokens(query))
        scored = []
        for i, counts in enumerate(self.counts):
            score = 0.0
            for term in terms & counts.keys():
                tf = counts[term]
                norm = tf + self.k1 * (1 - self.b + self.b * self.lengths[i] / (self.average or 1))
                score += self.weights[term] * tf * (self.k1 + 1) / norm
            if score > 0:
                scored.append((score, i))
        scored.sort(key=lambda pair: -pair[0])
        return [Hit(self.chunks[i], s, rank, "bm25") for rank, (s, i) in enumerate(scored[:k], start=1)]


def rrf(rankings: Sequence[Sequence[Hit]], k: int = 60, limit: int | None = None) -> list[Hit]:
    """Reciprocal rank fusion: only ranks count, so scores on different scales mix."""
    scores: dict[str, float] = {}
    chunks: dict[str, Chunk] = {}
    for ranking in rankings:
        for hit in ranking:
            scores[hit.chunk.id] = scores.get(hit.chunk.id, 0.0) + 1 / (k + hit.rank)
            chunks.setdefault(hit.chunk.id, hit.chunk)
    order = sorted(scores, key=lambda cid: -scores[cid])  # stable: ties keep first appearance
    order = order[:limit] if limit else order
    return [Hit(chunks[cid], scores[cid], rank, "rrf") for rank, cid in enumerate(order, start=1)]


class HybridSearch:
    def __init__(self, index: Index, keyword: BM25, depth: int = 10) -> None:
        self.index, self.keyword, self.depth = index, keyword, depth

    def search(self, query: str, k: int = 3) -> list[Hit]:
        return rrf([self.index.search(query, self.depth), self.keyword.search(query, self.depth)], limit=k)
