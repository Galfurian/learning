"""Measure the CPU cost of tev1 as a reranker, on the local machine only.

    uv run python scripts/measure_tev1_cpu.py [--questions 3] [--depth 10]

Small on purpose: tev1 on CPU takes seconds per request. Stop other models
first (ollama ps). Results: .cache/measurements/tev1-<mode>-cpu.json
"""

import argparse

from reranklab.corpus import DEV_QUESTIONS
from reranklab.costs import MEASUREMENTS, is_local, save_timing, time_tev1
from reranklab.evalset import load_questions
from reranklab.retriever import FirstStage, plant_chunks

p = argparse.ArgumentParser()
p.add_argument("--questions", type=int, default=3)
p.add_argument("--depth", type=int, default=10)
p.add_argument("--modes", default="A,B")
args = p.parse_args()
if not is_local():
    raise SystemExit("OLLAMA_HOST points to another machine: this script measures LOCAL CPU cost. Unset it.")
questions = [q for q in load_questions(DEV_QUESTIONS) if q.answerable][: args.questions]
stage = FirstStage("bm25", plant_chunks())  # no embedding model loaded: only tev1 uses memory
items = [(q.text, [h.chunk.text for h in stage.candidates(q.text, args.depth)]) for q in questions]
for mode in args.modes.split(","):
    timing = time_tev1(mode, items)
    save_timing(timing, MEASUREMENTS / f"tev1-{mode}-cpu.json")
    print(f"tev1 mode {mode}: {timing.pairs} pairs, {timing.requests} requests, {timing.seconds:.1f}s, "
          f"{timing.s_per_question}s/question, load {timing.load_seconds:.1f}s")
