"""Extract every prose chunk with one model, build the graph, score the links against gold.

    uv run python scripts/measure_extraction.py --model qwen3:1.7b

One model, one request at a time. Results are cached (.cache/scores), so a
crash loses at most one chunk; a second run only scores.
"""

import argparse
import time

from kglab.builder import build
from kglab.corpus import GOLD_GRAPH, load_notes
from kglab.extract import LINK_RELATIONS, extract
from kglab.graph import load
from kglab.metrics import triple_scores
from kglab.parse import load_models
from kglab.scorecache import ScoreCache

GLOSSARY_TYPES = ("Bay", "Item", "Pallet", "Mission", "Condition", "Incident")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--model", default="qwen3:1.7b")
    p.add_argument("--free", action="store_true", help="No enum on the relation (count invalid ones).")
    p.add_argument("--limit", type=int)
    args = p.parse_args()
    chunks = load_notes()[: args.limit]
    gold = load(GOLD_GRAPH)
    import json
    ambiguous = json.loads(GOLD_GRAPH.read_text())["ambiguous"]
    cache = ScoreCache()
    extractions, fresh, started = {}, [], time.perf_counter()
    for i, c in enumerate(chunks, 1):
        e = extract(c.title, c.text, model=args.model, constrained=not args.free, cache=cache)
        extractions[c.id] = e
        fresh.append(e.seconds)
        print(f"{i:3}/{len(chunks)} {c.id:32} {e.seconds:5.1f}s mentions={len(e.triples)} invalid={len(e.invalid)}", flush=True)
    tree = load_models()
    glossary = [n for n in gold.nodes.values() if n.type in GLOSSARY_TYPES]
    built, report = build(tree, glossary, chunks, extractions, ambiguous=ambiguous)
    ids = {c.id for c in chunks}
    gold_links = {(e.s, e.r, e.o) for e in gold.edges if e.r in LINK_RELATIONS and e.source in ids}
    built_links = {(e.s, e.r, e.o) for e in built.edges if e.r in LINK_RELATIONS}
    print(f"model {args.model}, seconds per chunk (first run) {sum(fresh) / len(fresh):.1f}, wall {time.perf_counter() - started:.0f}s")
    print(f"mentions {report.mentions}, kept {report.kept}, invalid {report.invalid}, unresolved {dict(report.unresolved)}, levels {dict(report.levels)}")
    for rel, s in triple_scores(built_links, gold_links).items():
        print(f"{rel:16} P {s.precision:.2f} R {s.recall:.2f} F1 {s.f1:.2f} ({s.tp}/{s.predicted} pred, {s.gold} gold)")


if __name__ == "__main__":
    main()
