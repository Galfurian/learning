"""Simulate a log of orders: low-level events plus a truth file next to them.

    uv run python scripts/simulate.py --orders 50 --seed 1 --out .cache/logs/demo.jsonl
"""

import argparse
import json
from pathlib import Path

from rich.console import Console

from pmlab.events import write_events
from pmlab.recipes import load_recipes
from pmlab.simulate import KINDS, simulate


def main() -> None:
    parser = argparse.ArgumentParser(description="Play the recipes out into a low-level event log.")
    parser.add_argument("--orders", type=int, default=50)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--mix", default="gadget=0.5,parts_test=0.3,brick_demo=0.2")
    parser.add_argument("--fail-p", type=float, default=0.15)
    parser.add_argument("--deviation", type=float, default=0.02, help="probability of each deviation kind")
    parser.add_argument("--out", type=Path, required=True, help="the .jsonl file; the truth goes next to it")
    args = parser.parse_args()
    mix = {k: float(v) for k, v in (part.split("=") for part in args.mix.split(","))}
    params = {"orders": args.orders, "seed": args.seed, "mix": mix, "fail_p": args.fail_p,
              "deviations": {kind: args.deviation for kind in KINDS}}
    events, truth = simulate(load_recipes(), **params)
    truth_path = args.out.with_suffix(".truth.json")
    write_events(args.out, {"log": args.out.stem, "truth": truth_path.name, "injected": []}, events)
    truth_path.write_text(json.dumps(truth, sort_keys=True, indent=1) + "\n", encoding="utf-8")
    Console(width=80).print(f"{len(events)} events, {len(truth['orders'])} orders -> {args.out}")


if __name__ == "__main__":
    main()
