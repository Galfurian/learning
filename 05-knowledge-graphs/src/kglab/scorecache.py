"""Copied from unit 04 (04-reranking/src/reranklab/scorecache.py).

The key is the sha256 of every part that can change a score: reranker id and
model revision, preprocessing version, scoring parameters, question, passage
(for tev1 mode B: the whole ordered passage list). Timing runs do not use it.
"""

import hashlib
import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .cache import UNIT_ROOT

DEFAULT_SCORE_DIR = UNIT_ROOT / ".cache" / "scores"


class ScoreCache:
    def __init__(self, directory: Path = DEFAULT_SCORE_DIR) -> None:
        self.directory = Path(directory)

    @staticmethod
    def key(parts: Sequence[str]) -> str:
        return hashlib.sha256("\x1f".join(parts).encode()).hexdigest()

    def _path(self, parts: Sequence[str]) -> Path:
        key = self.key(parts)
        return self.directory / key[:2] / f"{key}.json"

    def get(self, parts: Sequence[str]) -> Any | None:
        path = self._path(parts)
        return json.loads(path.read_text()) if path.exists() else None

    def put(self, parts: Sequence[str], value: Any) -> None:
        path = self._path(parts)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value))
