"""Copied from unit 04 (04-reranking/src/reranklab/bm25.py).

A cheap first stage: exact tokens, no model.
"""

import math
from collections import Counter
from collections.abc import Sequence

from .corpus import Chunk
from .embedders import tokens
from .index import Hit


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
