"""Measure retrieval on the dev set: one embedder per run (WSL rule).

uv run python scripts/measure_dev.py fake
uv run python scripts/measure_dev.py embeddinggemma [--no-prefix] [--size 60]
"""

import argparse
import json
import time

from raglab.cache import UNIT_ROOT, EmbeddingCache
from raglab.chunking import chunk_all
from raglab.corpus import DEV_MANUALS, load_manuals
from raglab.embedders import FakeEmbedder, OllamaEmbedder
from raglab.evalset import (
    by_category,
    evidence_at_k,
    first_relevant_rank,
    load_questions,
    mrr,
    recall_at_k,
    run_search,
)
from raglab.index import Index

parser = argparse.ArgumentParser()
parser.add_argument("model")
parser.add_argument("--no-prefix", action="store_true")
parser.add_argument("--size", type=int, default=60)
parser.add_argument("--overlap", type=int, default=15)
args = parser.parse_args()

embedder = FakeEmbedder() if args.model == "fake" else OllamaEmbedder(
    args.model, prefixed=not args.no_prefix, cache=EmbeddingCache()
)
chunks = chunk_all(load_manuals(DEV_MANUALS), args.size, args.overlap)
started = time.perf_counter()
index = Index.build(chunks, embedder)
build_seconds = time.perf_counter() - started
questions = load_questions()
results = run_search(questions, index.search, 10)

report = {
    "embedder": embedder.name, "size": args.size, "overlap": args.overlap, "chunks": len(chunks),
    "build_seconds": round(build_seconds, 2),
    "R@1": recall_at_k(questions, results, 1), "R@3": recall_at_k(questions, results, 3),
    "E@3": evidence_at_k(questions, results, 3), "MRR": round(mrr(questions, results), 3),
    "by_category@3": by_category(questions, results, 3),
    "top1_answerable": sorted(round(results[q.id][0].score, 3) for q in questions if q.answerable),
    "top1_no_answer": sorted(round(results[q.id][0].score, 3) for q in questions if not q.answerable),
    "misses@3": [
        (q.id, first_relevant_rank(results[q.id], q.relevant), [h.chunk.id for h in results[q.id][:3]])
        for q in questions if q.answerable and not (first_relevant_rank(results[q.id], q.relevant) or 99) <= 3
    ],
}
print(json.dumps(report, indent=1))
out = UNIT_ROOT / ".cache" / "measurements"
out.mkdir(parents=True, exist_ok=True)
name = f"{args.model.replace(':', '_')}{'-noprefix' if args.no_prefix else ''}-s{args.size}.json"
(out / name).write_text(json.dumps(report, indent=1))
