"""The index: one matrix of unit vectors, and the chunk behind each row.

Search is one matrix-vector product. A vector database does the same job
with approximate search, filters and persistence, for millions of rows.
"""

from dataclasses import dataclass

import numpy as np

from .corpus import Chunk
from .embedders import Embedder


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float
    rank: int
    kind: str = "cosine"


class Index:
    def __init__(self, chunks: list[Chunk], vectors: np.ndarray, embedder: Embedder) -> None:
        if len(chunks) != len(vectors):
            raise ValueError(f"{len(chunks)} chunks but {len(vectors)} vectors")
        norms = np.linalg.norm(vectors, axis=1) if len(vectors) else np.zeros(0)
        bad = ~(np.isclose(norms, 1.0, atol=1e-3) | (norms == 0.0))
        if bad.any():
            raise ValueError(
                f"{embedder.name}: {int(bad.sum())} vectors are not unit length "
                f"(first norm {float(norms[bad][0]):.3f}). The index expects normalized vectors."
            )
        self.chunks = list(chunks)
        self.vectors = vectors.astype(np.float32)
        self.embedder = embedder
        self.ids = [c.id for c in chunks]
        self._by_id = {c.id: c for c in chunks}

    @classmethod
    def build(cls, chunks: list[Chunk], embedder: Embedder) -> "Index":
        vectors = embedder.embed_documents([c.text for c in chunks], [c.title for c in chunks])
        return cls(chunks, vectors, embedder)

    def by_id(self, chunk_id: str) -> Chunk:
        return self._by_id[chunk_id]

    def search_vector(self, vector: np.ndarray, k: int = 3) -> list[Hit]:
        if k < 1:
            raise ValueError("k must be at least 1")
        if not self.chunks:
            return []
        # Unit vectors: the dot product is the cosine.
        scores = self.vectors @ np.asarray(vector, dtype=np.float32)
        order = np.argsort(-scores, kind="stable")[:k]
        return [Hit(self.chunks[i], float(scores[i]), rank) for rank, i in enumerate(order, start=1)]

    def search(self, query: str, k: int = 3) -> list[Hit]:
        return self.search_vector(self.embedder.embed_query(query), k)
