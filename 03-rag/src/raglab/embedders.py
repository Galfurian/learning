"""Two embedders with the same interface.

- ``OllamaEmbedder``: a real embedding model behind POST /api/embed.
- ``FakeEmbedder``: hashed word counts. No model, deterministic. The checks
  use it, and it is the lexical baseline: it matches words, not meaning.
"""

import re
import zlib
from typing import Protocol

import numpy as np

from .cache import EmbeddingCache
from .client import DEFAULT_EMBED_MODEL, Tracer, embed

STOPWORDS = frozenset(
    """a an the is are was were be been being of to in on at for with and or not no
    do does did i my me we our you your it its this that these those what which who
    how when where why can should could would will shall from by as if then than so
    up out about after before there here have has had any some""".split()
)

# Words, numbers and identifiers: "e-4021", "pn-x7q-991-a", "0.8", "m/s" stay whole.
TOKEN = re.compile(r"[a-z0-9]+(?:[-./][a-z0-9]+)*")


def tokens(text: str) -> list[str]:
    return [token for token in TOKEN.findall(text.lower()) if token not in STOPWORDS]


# The query and document formats documented by each model.
PREFIXES: dict[str, tuple[str, str]] = {
    "embeddinggemma": ("task: search result | query: {text}", "title: {title} | text: {text}"),
    "nomic-embed-text": ("search_query: {text}", "search_document: {text}"),
    "qwen3-embedding:0.6b": (
        "Instruct: Given a question, retrieve manual passages that answer it\nQuery: {text}",
        "{text}",
    ),
}


class Embedder(Protocol):
    name: str

    def embed_documents(self, texts: list[str], titles: list[str] | None = None) -> np.ndarray: ...

    def embed_query(self, text: str) -> np.ndarray: ...


class FakeEmbedder:
    """Bag of words in a fixed dimension: word -> crc32(word) % dim, counted."""

    def __init__(self, dim: int = 1024, normalized: bool = True) -> None:
        self.dim = dim
        self.normalized = normalized
        self.name = "fake (bag of words)"

    def vector(self, text: str) -> np.ndarray:
        vector = np.zeros(self.dim, dtype=np.float32)
        for token in tokens(text):
            vector[zlib.crc32(token.encode("utf-8")) % self.dim] += 1.0
        if self.normalized:
            norm = float(np.linalg.norm(vector))
            if norm > 0:
                vector /= norm
        return vector

    def embed_documents(self, texts: list[str], titles: list[str] | None = None) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        return np.stack([self.vector(text) for text in texts])

    def embed_query(self, text: str) -> np.ndarray:
        return self.vector(text)


class OllamaEmbedder:
    def __init__(
        self,
        model: str = DEFAULT_EMBED_MODEL,
        *,
        prefixed: bool = True,
        cache: EmbeddingCache | None = None,
        tracer: Tracer | None = None,
        batch: int = 16,
    ) -> None:
        self.model = model
        self.prefixed = prefixed
        self.cache = cache
        self.tracer = tracer
        self.batch = batch
        self.calls = 0
        self.cached = 0
        base = model.removesuffix(":latest")
        self.formats = PREFIXES.get(base) if prefixed else None
        self.name = model if prefixed else f"{model} (prefixes off)"

    def format_query(self, text: str) -> str:
        return self.formats[0].format(text=text) if self.formats else text

    def format_document(self, text: str, title: str | None) -> str:
        if not self.formats:
            return text
        return self.formats[1].format(text=text, title=title or "none")

    def _embed(self, texts: list[str], cache: EmbeddingCache | None) -> np.ndarray:
        vectors: list[np.ndarray | None] = [cache.get(self.model, text) if cache else None for text in texts]
        self.cached += sum(vector is not None for vector in vectors)
        missing = [i for i, vector in enumerate(vectors) if vector is None]
        # Small batches: long CPU requests have crashed WSL before.
        for start in range(0, len(missing), self.batch):
            chunk = missing[start : start + self.batch]
            result = embed(self.model, [texts[i] for i in chunk], tracer=self.tracer)
            self.calls += 1
            for i, values in zip(chunk, result.vectors):
                vector = np.asarray(values, dtype=np.float32)
                vectors[i] = vector
                if cache:
                    cache.put(self.model, texts[i], vector)
        if not vectors:
            return np.zeros((0, 0), dtype=np.float32)
        return np.stack(vectors)

    def embed_documents(self, texts: list[str], titles: list[str] | None = None) -> np.ndarray:
        titles = titles or [None] * len(texts)
        return self._embed([self.format_document(t, h) for t, h in zip(texts, titles)], self.cache)

    def embed_query(self, text: str) -> np.ndarray:
        # Not cached: one short request, and --verbose should always show it.
        return self._embed([self.format_query(text)], None)[0]
