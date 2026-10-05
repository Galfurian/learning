"""Command line and setup shared by every exercises/*/exeNN.py file."""

import argparse
from collections.abc import Sequence

from . import ui
from .cache import EmbeddingCache
from .chunking import DEFAULT_OVERLAP, DEFAULT_SIZE, Chunker, chunk_all
from .client import DEFAULT_CHAT_MODEL, DEFAULT_EMBED_MODEL, Tracer
from .context import DEFAULT_BUDGET
from .corpus import DEV_MANUALS, Chunk, load_manuals
from .embedders import Embedder, FakeEmbedder, OllamaEmbedder
from .evalset import Question
from .hybrid import BM25, HybridSearch
from .index import Index


def parser(description: str, *, generation: bool = False, evaluation: bool = True) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--question", help="Ask this question instead of the eval set.")
    p.add_argument("--case", type=int, help="Run only question N of the eval set (1-based).")
    p.add_argument("--top-k", type=int, default=3, help="Number of chunks to retrieve.")
    p.add_argument("--embed-model", default=DEFAULT_EMBED_MODEL, help="Embedding model.")
    p.add_argument("--fake-embed", action="store_true", help="Use the FakeEmbedder (bag of words).")
    p.add_argument("--no-prefix", action="store_true", help="Embed without the documented prefixes.")
    p.add_argument("--size", type=int, default=DEFAULT_SIZE, help="Chunk size in words.")
    p.add_argument("--overlap", type=int, default=DEFAULT_OVERLAP, help="Chunk overlap in words.")
    if evaluation:
        p.add_argument("--eval", action="store_true", help="Run the whole eval set and print the metrics.")
    if generation:
        p.add_argument("--model", default=DEFAULT_CHAT_MODEL, help="Generative model.")
        p.add_argument("--budget", type=int, default=DEFAULT_BUDGET, help="Context budget in estimated tokens.")
        p.add_argument("--think", action="store_true", help="Let the generator reason first.")
        p.add_argument("--show-raw", action="store_true", help="Show the exact rendered prompt.")
        p.add_argument("--record", help="Write one JSON trace per question to this folder (EXE08).")
        p.add_argument("--min-score", type=float, help="Drop hits below this score before building the context.")
        p.add_argument("--retriever", choices=["semantic", "keyword", "hybrid"], default="semantic",
                       help="How the APP finds chunks.")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--verbose", action="store_true", help="Show every HTTP request and response.")
    mode.add_argument("--inspect", action="store_true", help="Show chunks and requests without calling a model.")
    return p


def tracer(args: argparse.Namespace) -> Tracer | None:
    return ui.show_http if getattr(args, "verbose", False) else None


def make_embedder(args: argparse.Namespace) -> Embedder:
    if args.fake_embed:
        return FakeEmbedder()
    return OllamaEmbedder(args.embed_model, prefixed=not args.no_prefix, cache=EmbeddingCache(), tracer=tracer(args))


def make_search(args: argparse.Namespace, index: Index):
    choice = getattr(args, "retriever", "semantic")
    if choice == "keyword":
        return BM25(index.chunks).search
    if choice == "hybrid":
        return HybridSearch(index, BM25(index.chunks)).search
    return index.search


def dev_chunks(args: argparse.Namespace, chunker: Chunker | None = None) -> list[Chunk]:
    return chunk_all(load_manuals(DEV_MANUALS), args.size, args.overlap, chunker=chunker)


def dev_index(args: argparse.Namespace, chunks: list[Chunk] | None = None) -> Index:
    embedder = make_embedder(args)
    index = Index.build(chunks if chunks is not None else dev_chunks(args), embedder)
    if isinstance(embedder, OllamaEmbedder):
        ui.show_note(f"index: {len(index.chunks)} chunks, {embedder.cached} vectors from the cache, "
                     f"{embedder.calls} request(s) to {embedder.model}")
    return index


def select_questions(args: argparse.Namespace, questions: Sequence[Question]) -> list[Question]:
    if args.question:
        return [Question("free", args.question, frozenset(), "free", "", ())]
    if args.case is not None:
        if not 1 <= args.case <= len(questions):
            raise SystemExit(f"--case must be between 1 and {len(questions)}")
        return [questions[args.case - 1]]
    return list(questions)


def todo(function_name: str, why: str) -> None:
    ui.show_todo(function_name, why)
