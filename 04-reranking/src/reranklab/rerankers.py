"""The second stage: reads the question and a passage together, returns a relevance score.

A relevance score orders candidates. It is not a probability: the
cross-encoder gives a logit (a sigmoid of it is still not calibrated), and the
tev1 noul value has its own scale.
"""

import json
import random
import time
from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Protocol

import numpy as np

from .client import DEFAULT_DECISION_MODEL, Tracer, decide
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
BGE = CrossEncoderSpec("bge", "Xenova/bge-reranker-base", "onnx/model_quantized.onnx",
                       "280bcc27a84e0b898c251e06fddb25171bd9b101")


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


# ---------------------------------------------------------------- tev1

INSTRUCTION_A = "Does the passage contain the answer to the question?"
QUESTION_A = {"relevant": {"type": "noul", "instructions": INSTRUCTION_A}}


def state_a(question: str, passage: str) -> str:
    return f"Question: {question}\n\nPassage:\n{passage}"


def state_b(question: str, passages: Sequence[str]) -> str:
    body = "\n\n".join(f"Passage {i}:\n{p}" for i, p in enumerate(passages, start=1))
    return f"Question: {question}\n\n{body}"


def questions_b(n: int) -> dict:
    return {
        f"p{i}": {"type": "noul", "instructions": f"Does passage {i} contain the answer to the question?"}
        for i in range(1, n + 1)
    }


class Tev1Reranker:
    """Mode A: one request per passage (independent judgments).
    Mode B: one request, one noul question per passage, all sharing one state:
    a different problem, where passages and their positions influence each other.
    """

    def __init__(self, model: str = DEFAULT_DECISION_MODEL, *, mode: str = "A", order: str = "original",
                 seed: int = 0, cache: ScoreCache | None = None, tracer: Tracer | None = None) -> None:
        if mode not in ("A", "B") or order not in ("original", "reversed", "shuffled"):
            raise ValueError("mode must be A or B; order original, reversed or shuffled")
        self.model, self.mode, self.order, self.seed = model, mode, order, seed
        self.cache, self.tracer = cache, tracer
        self.requests = 0
        self.id = f"tev1:{model}/mode-{mode}" + (f"/{order}-{seed}" if mode == "B" else "")

    def _ask(self, state: str, questions: dict) -> dict[str, float]:
        self.requests += 1
        answers = decide(self.model, state, questions, tracer=self.tracer).answers
        return {name: float(a["noul"]) for name, a in answers.items()}

    def score(self, question: str, passages: list[str]) -> list[float]:
        if self.mode == "A":
            out = []
            for p in passages:
                parts = [self.id, INSTRUCTION_A, question, p]
                value = self.cache.get(parts) if self.cache else None
                if value is None:
                    value = self._ask(state_a(question, p), QUESTION_A)["relevant"]
                    if self.cache:
                        self.cache.put(parts, value)
                out.append(value)
            return out
        positions = list(range(len(passages)))
        if self.order == "reversed":
            positions.reverse()
        elif self.order == "shuffled":
            random.Random(self.seed).shuffle(positions)
        shown = [passages[i] for i in positions]
        parts = [self.id, json.dumps(questions_b(len(shown)), sort_keys=True), question, *shown]
        scores = self.cache.get(parts) if self.cache else None
        if scores is None:
            answers = self._ask(state_b(question, shown), questions_b(len(shown)))
            scores = [answers[f"p{j}"] for j in range(1, len(shown) + 1)]
            if self.cache:
                self.cache.put(parts, scores)
        out = [0.0] * len(passages)
        for shown_index, original_index in enumerate(positions):
            out[original_index] = scores[shown_index]
        return out


def make_reranker(name: str, *, tracer: Tracer | None = None, cache: bool = True) -> Reranker | None:
    store = ScoreCache() if cache else None
    if name == "none":
        return None
    if name == "fake":
        return FakeReranker()
    if name == "minilm":
        return CrossEncoderReranker(MINILM, cache=store)
    if name == "bge":
        return CrossEncoderReranker(BGE, cache=store)
    if name in ("tev1-a", "tev1-b"):
        return Tev1Reranker(mode=name[-1].upper(), cache=store, tracer=tracer)
    raise ValueError(f"unknown reranker {name!r}")
