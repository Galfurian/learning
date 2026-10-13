"""Copied from unit 04 (04-reranking/src/reranklab/rerankers.py), trimmed to the MiniLM cross-encoder.

A relevance score orders candidates. It is not a probability: the
cross-encoder gives a logit (a sigmoid of it is still not calibrated).
"""

import time
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Protocol

import numpy as np

from .client import Tracer
from .embedders import tokens
from .index import Hit
from .scorecache import ScoreCache


class Reranker(Protocol):
    id: str

    def score(self, question: str, passages: list[str]) -> list[float]: ...


def rerank(question: str, hits: Sequence[Hit], reranker: Reranker, k: int) -> list[Hit]:
    """Score every candidate, sort by score (stable on ties), keep k. Nothing new is added."""
    scores = reranker.score(question, [h.chunk.text for h in hits])
    order = sorted(range(len(hits)), key=lambda i: -scores[i])
    return [
        replace(hits[i], rank=rank, kind="rerank", rerank_score=float(scores[i]),
                first_rank=hits[i].first_rank or hits[i].rank)
        for rank, i in enumerate(order[:k], start=1)
    ]


class FakeReranker:
    """Share of the question's tokens found in the passage. Deterministic, no model."""

    id = "fake"

    def score(self, question: str, passages: list[str]) -> list[float]:
        wanted = set(tokens(question))
        return [len(wanted & set(tokens(p))) / (len(wanted) or 1) for p in passages]


# ---------------------------------------------------------------- cross-encoder

PREPROCESSING_VERSION = "pair-v1"  # change it when pair formatting, max_length or truncation change


@dataclass(frozen=True)
class CrossEncoderSpec:
    name: str
    repo: str
    file: str
    revision: str
    max_length: int = 512
    intra_threads: int = 4
    inter_threads: int = 1


MINILM = CrossEncoderSpec("minilm", "Xenova/ms-marco-MiniLM-L-6-v2", "onnx/model.onnx",
                          "a09144355adeed5f58c8ed011d209bf8ee5a1fec")


class CrossEncoderReranker:
    """(question, passage) -> tokens -> one ONNX forward pass -> one logit."""

    def __init__(self, spec: CrossEncoderSpec, *, cache: ScoreCache | None = None, batch: int = 1) -> None:
        self.spec = spec
        self.cache = cache
        self.batch = batch
        self.id = f"{spec.name}@{spec.revision[:12]}/{PREPROCESSING_VERSION}/len{spec.max_length}"
        self.load_seconds = 0.0
        self._tokenizer = None
        self._session = None

    def _load(self) -> None:
        if self._session is not None:
            return
        import onnxruntime as ort
        from huggingface_hub import hf_hub_download
        from tokenizers import Tokenizer

        started = time.perf_counter()
        try:
            tokenizer_path = hf_hub_download(self.spec.repo, "tokenizer.json", revision=self.spec.revision)
            model_path = hf_hub_download(self.spec.repo, self.spec.file, revision=self.spec.revision)
        except Exception as exc:  # network, missing revision, gated repo
            raise RuntimeError(
                f"cannot download {self.spec.repo}@{self.spec.revision[:12]} ({exc.__class__.__name__}). "
                "Check the network, or the Hugging Face cache."
            ) from None
        tokenizer = Tokenizer.from_file(tokenizer_path)
        tokenizer.enable_truncation(self.spec.max_length)  # longest_first
        options = ort.SessionOptions()
        options.intra_op_num_threads = self.spec.intra_threads
        options.inter_op_num_threads = self.spec.inter_threads
        self._tokenizer = tokenizer
        self._session = ort.InferenceSession(model_path, options, providers=["CPUExecutionProvider"])
        self.load_seconds = time.perf_counter() - started

    def _feed(self, encodings) -> dict[str, np.ndarray]:
        width = max(len(e.ids) for e in encodings)

        def pad(rows):
            return np.array([r + [0] * (width - len(r)) for r in rows], dtype=np.int64)

        names = {i.name for i in self._session.get_inputs()}
        feed = {"input_ids": pad([e.ids for e in encodings]),
                "attention_mask": pad([e.attention_mask for e in encodings])}
        if "token_type_ids" in names:
            feed["token_type_ids"] = pad([e.type_ids for e in encodings])
        return feed

    def score_pair(self, question: str, passage: str) -> float:
        if self._session is None:
            self._load()
        logits = self._session.run(None, self._feed([self._tokenizer.encode(question, passage)]))[0]
        return float(np.asarray(logits).reshape(-1)[0])

    def score(self, question: str, passages: list[str]) -> list[float]:
        out: list[float | None] = [
            self.cache.get([self.id, "", question, p]) if self.cache else None for p in passages
        ]
        todo = [i for i, v in enumerate(out) if v is None]
        if todo:
            self._load()
        for start in range(0, len(todo), self.batch):
            chunk = todo[start : start + self.batch]
            encodings = [self._tokenizer.encode(question, passages[i]) for i in chunk]
            logits = np.asarray(self._session.run(None, self._feed(encodings))[0]).reshape(-1)
            for i, value in zip(chunk, logits):
                out[i] = float(value)
                if self.cache:
                    self.cache.put([self.id, "", question, passages[i]], float(value))
        return out


def make_reranker(name: str, *, tracer: Tracer | None = None, cache: bool = True) -> Reranker | None:
    store = ScoreCache() if cache else None
    if name == "none":
        return None
    if name == "fake":
        return FakeReranker()
    if name == "minilm":
        return CrossEncoderReranker(MINILM, cache=store)
    raise ValueError(f"unknown reranker {name!r}")
