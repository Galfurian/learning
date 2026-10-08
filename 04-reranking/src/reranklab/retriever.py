"""The first stage: cheap, scores every chunk alone, returns N candidates.

nomic   nomic-embed-text (default: measured headroom for a reranker)
gemma   embeddinggemma (strong: little left to rerank)
bm25    exact tokens, no model
fake    hashed word counts, no model
"""

from dataclasses import replace

from .bm25 import BM25
from .cache import EmbeddingCache
from .chunking import chunk_all
from .client import Tracer
from .corpus import Chunk, PLANT_MANUALS, load_manuals
from .embedders import FakeEmbedder, OllamaEmbedder
from .index import Hit, Index

EMBED_MODELS = {"nomic": "nomic-embed-text", "gemma": "embeddinggemma"}


def plant_chunks() -> list[Chunk]:
    return chunk_all(load_manuals(PLANT_MANUALS), 60, 15)


class FirstStage:
    def __init__(self, name: str, chunks: list[Chunk], *, tracer: Tracer | None = None) -> None:
        self.name = name
        self.chunks = chunks
        if name == "bm25":
            self._search = BM25(chunks).search
        elif name == "fake":
            self._search = Index.build(chunks, FakeEmbedder()).search
        elif name in EMBED_MODELS:
            embedder = OllamaEmbedder(EMBED_MODELS[name], cache=EmbeddingCache(), tracer=tracer)
            self._search = Index.build(chunks, embedder).search
        else:
            raise ValueError(f"unknown first stage {name!r}")

    def candidates(self, question: str, depth: int) -> list[Hit]:
        # BM25 can return fewer than depth: only chunks that share a token.
        return [replace(h, first_rank=h.rank) for h in self._search(question, depth)]
