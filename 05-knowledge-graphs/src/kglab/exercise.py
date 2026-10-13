"""Adapted from unit 04 (04-reranking/src/reranklab/exercise.py): the shared command line."""

import argparse
from collections.abc import Sequence

from . import ui
from .client import DEFAULT_CHAT_MODEL, Tracer
from .evalset import Question

PIPELINES = ("chunks", "gold", "built")


def parser(description: str, *, generation: bool = False, extraction: bool = False) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=description)
    p.add_argument("--question", help="Ask this question instead of the dev set.")
    p.add_argument("--case", type=int, help="Run only question N of the dev set (1-based).")
    p.add_argument("--eval", action="store_true", help="Run the whole set and print the metrics.")
    if extraction:
        p.add_argument("--extract-model", default=DEFAULT_CHAT_MODEL, help="Model that extracts the links.")
    if generation:
        p.add_argument("--model", default=DEFAULT_CHAT_MODEL, help="Generative model.")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--verbose", action="store_true", help="Show every request and response.")
    mode.add_argument("--inspect", action="store_true", help="Show the setup without calling a model.")
    return p


def tracer(args: argparse.Namespace) -> Tracer | None:
    return ui.show_http if getattr(args, "verbose", False) else None


def select_questions(args: argparse.Namespace, questions: Sequence[Question]) -> list[Question]:
    if getattr(args, "eval", False) and (args.case is not None or args.question):
        raise SystemExit("--eval runs the whole set: drop --case and --question.")
    if args.question:
        return [Question("free", args.question, "free", None, ())]
    if args.case is not None:
        if not 1 <= args.case <= len(questions):
            raise SystemExit(f"--case must be between 1 and {len(questions)}")
        return [questions[args.case - 1]]
    return list(questions)
