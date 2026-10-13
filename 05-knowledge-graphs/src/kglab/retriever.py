"""Adapted from unit 04 (04-reranking/src/reranklab/retriever.py): chunk RAG, pipeline A.

The corpus is every prose chunk plus the data models rendered as text
(parse.model_chunks): what a RAG system over the same documents reads. The
best unit 04 setting on a CPU: a cheap first stage, then MiniLM.
"""

from dataclasses import replace

from .bm25 import BM25
from .cache import EmbeddingCache
from .client import Tracer
from .corpus import Chunk, load_notes
from .embedders import FakeEmbedder, OllamaEmbedder
from .index import Hit, Index
from .parse import model_chunks
from .rerankers import rerank, make_reranker

EMBED_MODELS = {"nomic": "nomic-embed-text"}
FIRST_STAGES = ("bm25", "nomic", "fake")


def line_chunks() -> list[Chunk]:
    return load_notes() + model_chunks()


class ChunkRetriever:
    def __init__(self, first_stage: str = "bm25", reranker: str = "minilm", *, depth: int = 20,
                 chunks: list[Chunk] | None = None, tracer: Tracer | None = None) -> None:
        self.chunks = chunks if chunks is not None else line_chunks()
        self.depth = depth
        if first_stage == "bm25":
            self._search = BM25(self.chunks).search
        elif first_stage == "fake":
            self._search = Index.build(self.chunks, FakeEmbedder()).search
        elif first_stage in EMBED_MODELS:
            embedder = OllamaEmbedder(EMBED_MODELS[first_stage], cache=EmbeddingCache(), tracer=tracer)
            self._search = Index.build(self.chunks, embedder).search
        else:
            raise ValueError(f"unknown first stage {first_stage!r}")
        self.reranker = make_reranker(reranker, tracer=tracer)

    def top(self, question: str, k: int = 3) -> list[Hit]:
        hits = [replace(h, first_rank=h.rank) for h in self._search(question, self.depth)]
        if self.reranker is None:
            return hits[:k]
        return rerank(question, hits, self.reranker, k)
