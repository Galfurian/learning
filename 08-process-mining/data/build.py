"""Write the committed logs, deterministically.

    uv run python data/build.py            # into data/
    uv run python data/build.py --out DIR  # somewhere else (the test compares the two)

logs/train and logs/holdout are simulated (src/pmlab/simulate.py), with the
true order of each event in <name>.truth.json next to the log. orders/ref-*
are the reference order and its injected copies; their header holds the
order truth and the injected faults.
"""

import argparse
import json
from pathlib import Path

from pmlab.events import write_events
from pmlab.recipes import load_recipes
from pmlab.simulate import KINDS, reference_logs, simulate

HERE = Path(__file__).parent
LOGS = {
    "train": {"orders": 200, "seed": 8, "mix": {"gadget": 0.5, "parts_test": 0.3, "brick_demo": 0.2},
              "fail_p": 0.15, "deviations": {kind: 0.02 for kind in KINDS}},
    "holdout": {"orders": 60, "seed": 80, "mix": {"gadget": 0.4, "parts_test": 0.4, "brick_demo": 0.2},
                "fail_p": 0.25, "deviations": {kind: 0.04 for kind in KINDS}},
}


def write_log(out: Path, name: str, params: dict, recipes) -> None:
    events, truth = simulate(recipes, **params)
    injected = [{"kind": d["kind"], "operation": d["operation"]}
                for order in truth["orders"].values() for d in order["deviations"]]
    header = {"log": name, "truth": f"{name}.truth.json", "params": params, "injected": injected}
    write_events(out / "logs" / f"{name}.jsonl", header, events)
    (out / "logs" / f"{name}.truth.json").write_text(json.dumps(truth, sort_keys=True, indent=1) + "\n",
                                                     encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=HERE)
    args = parser.parse_args()
    recipes = load_recipes()
    for name, params in LOGS.items():
        write_log(args.out, name, params, recipes)
    for name, (header, events) in reference_logs(recipes).items():
        write_events(args.out / "orders" / f"{name}.jsonl", header, events)


if __name__ == "__main__":
    main()
