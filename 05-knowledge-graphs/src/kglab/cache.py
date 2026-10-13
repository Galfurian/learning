"""Copied from unit 04 (04-reranking/src/reranklab/cache.py).

Embedding a corpus on CPU takes seconds to minutes. The key covers the model
and the exact text sent (prefix included), so any change re-embeds only what
changed, and nothing stale is ever reused.
"""

import hashlib
import re
from pathlib import Path

import numpy as np

UNIT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CACHE_DIR = UNIT_ROOT / ".cache" / "embeddings"


class EmbeddingCache:
    def __init__(self, directory: Path = DEFAULT_CACHE_DIR) -> None:
        self.directory = Path(directory)

    @staticmethod
    def key(model: str, text: str) -> str:
        return hashlib.sha256(f"{model}\n{text}".encode()).hexdigest()

    def _path(self, model: str, text: str) -> Path:
        folder = re.sub(r"[^A-Za-z0-9._-]", "_", model)
        return self.directory / folder / f"{self.key(model, text)}.npy"

    def get(self, model: str, text: str) -> np.ndarray | None:
        path = self._path(model, text)
        return np.load(path) if path.exists() else None

    def put(self, model: str, text: str, vector: np.ndarray) -> None:
        path = self._path(model, text)
        path.parent.mkdir(parents=True, exist_ok=True)
        np.save(path, np.asarray(vector, dtype=np.float32))
