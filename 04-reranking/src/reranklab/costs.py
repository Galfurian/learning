"""What reranking costs, measured, with the place it was measured.

CPU  the local machine (OLLAMA_HOST unset or local), small batches, one model loaded
GPU  a remote Ollama (OLLAMA_HOST), labeled; never reported as a CPU cost
"""

import json
import socket
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.parse import urlparse

from .cache import UNIT_ROOT
from .client import DEFAULT_DECISION_MODEL, ollama_url
from .rerankers import CrossEncoderReranker, CrossEncoderSpec, Tev1Reranker

MEASUREMENTS = UNIT_ROOT / ".cache" / "measurements"


@dataclass
class Timing:
    name: str
    where: str
    pairs: int
    questions: int
    requests: int
    seconds: float
    load_seconds: float

    @property
    def ms_per_pair(self) -> float:
        return round(1000 * self.seconds / self.pairs, 1) if self.pairs else 0.0

    @property
    def s_per_question(self) -> float:
        return round(self.seconds / self.questions, 2) if self.questions else 0.0


LOCAL_HOSTS = {"127.0.0.1", "localhost", "0.0.0.0", "::1", socket.gethostname()}


def is_local() -> bool:
    """Is the Ollama server this machine? (An SSH tunnel to another machine still looks local.)"""
    return urlparse(ollama_url()).hostname in LOCAL_HOSTS


def time_cross_encoder(spec: CrossEncoderSpec, items: list[tuple[str, list[str]]], *, batch: int = 1,
                       warmup: int = 3) -> Timing:
    reranker = CrossEncoderReranker(spec, cache=None, batch=batch)
    reranker._load()
    question, passages = items[0]
    for passage in passages[:warmup]:
        reranker.score_pair(question, passage)
    started = time.perf_counter()
    pairs = 0
    for question, passages in items:
        reranker.score(question, passages)
        pairs += len(passages)
    return Timing(f"{spec.name}-batch{batch}", "CPU", pairs, len(items), 0,
                  time.perf_counter() - started, reranker.load_seconds)


def time_tev1(mode: str, items: list[tuple[str, list[str]]], *, model: str = DEFAULT_DECISION_MODEL) -> Timing:
    reranker = Tev1Reranker(model, mode=mode, cache=None)
    started = time.perf_counter()
    reranker.score(items[0][0], items[0][1][:1])  # loads the model: reported apart
    load = time.perf_counter() - started
    reranker.requests = 0
    started = time.perf_counter()
    pairs = 0
    for question, passages in items:
        reranker.score(question, passages)
        pairs += len(passages)
    where = "CPU" if is_local() else f"GPU ({ollama_url()})"
    return Timing(f"tev1-{mode}", where, pairs, len(items), reranker.requests, time.perf_counter() - started, load)


def save_timing(timing: Timing, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(timing), indent=1))


def load_timing(path: Path) -> Timing | None:
    return Timing(**json.loads(path.read_text())) if path.exists() else None


def best_under_budget(rows: list[dict], budget_s: float) -> dict | None:
    fits = [r for r in rows if r["s/question"] <= budget_s]
    if not fits:
        return None
    return max(fits, key=lambda r: (r["evidence_recall@1"], r["nDCG@3"], -r["s/question"]))


def reranker_cpu_seconds(name: str, records: list[dict], directory: Path = MEASUREMENTS) -> float | None:
    """CPU seconds per question for a recorded run, from the CPU measurements (None if not measured).

    name: "embedding" (no reranker), "minilm", "bge" or "tev1"; each question costs
    its own number of candidates times the measured time per pair.
    """
    if name == "embedding":
        return 0.0
    file = {"minilm": "minilm-cpu.json", "bge": "bge-cpu.json", "tev1": "tev1-A-cpu.json"}.get(name)
    timing = load_timing(directory / file) if file else None
    if timing is None or not timing.pairs:
        return None
    pairs = sum(len(r["candidates"]) for r in records) / len(records)
    return timing.seconds / timing.pairs * pairs
