"""Record benchmark rows on the dev set for EXE07.

    uv run python scripts/record_rows.py --first-stage nomic --depth 5 --reranker minilm --top-k 3 --out DIR
"""

import argparse
import json
from pathlib import Path

from reranklab.benchmark import diagnose, row, run_question
from reranklab.corpus import DEV_QUESTIONS
from reranklab.evalset import load_questions
from reranklab.rerankers import make_reranker
from reranklab.retriever import FirstStage, plant_chunks

p = argparse.ArgumentParser()
p.add_argument("--first-stage", default="nomic")
p.add_argument("--depth", type=int, default=20)
p.add_argument("--reranker", default="minilm")
p.add_argument("--top-k", type=int, default=3)
p.add_argument("--model", default="qwen3:1.7b")
p.add_argument("--out", required=True)
args = p.parse_args()
out = Path(args.out)
out.mkdir(parents=True, exist_ok=True)
stage = FirstStage(args.first_stage, plant_chunks())
reranker = make_reranker(args.reranker)
for q in load_questions(DEV_QUESTIONS):
    record = row(run_question(q, stage, reranker, depth=args.depth, k=args.top_k, model=args.model))
    record["settings"] = vars(args) | {"out": None}
    record["question"] = q.text
    record["expected"] = diagnose(record)
    (out / f"{q.id}.json").write_text(json.dumps(record, indent=1, ensure_ascii=False))
    print(q.id, record["expected"])
