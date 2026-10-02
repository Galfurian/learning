"""EXE08 — a production line with a decision-model supervisor. A demo: read it, run it."""

import argparse
import logging

import recipes
from line import Line
from line.machines import Conveyor, Feeder, Inspection, Mill
from supervisor import report
from supervisor.policy import Policy
from supervisor.state import RawWindow, Summary
from supervisor.strategy import Flat, TwoStep
from supervisor.supervisor import Supervisor
from supervisor.symptoms import LowThroughput, Monitor, RejectRate
from supervisor.view import View

from declab.client import DEFAULT_MODEL

# The line: machines in order, each with its name.
LAYOUT = [
    ("F1", Feeder),
    ("C1", Conveyor),
    ("M1", Mill),
    ("Q1", Inspection),
]

# What code watches. Detecting a problem needs no model.
DETECTORS = [
    RejectRate("Q1", max_rejects=2),
    LowThroughput("Q1", min_parts=7),
]

STATES = {"summary": Summary, "raw": RawWindow}
STRATEGIES = {"two-step": TwoStep, "flat": Flat}
RECIPES = {"default": recipes.DEFAULT, "quiet": recipes.QUIET}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state", choices=STATES, default="summary", help="How logs become the state.")
    parser.add_argument("--strategy", choices=STRATEGIES, default="two-step", help="How the questions are asked.")
    parser.add_argument("--recipe", choices=RECIPES, default="default")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--verbose", action="store_true", help="Show every state sent to the model.")
    args = parser.parse_args()
    logging.getLogger("httpx").setLevel(logging.WARNING)

    line = Line(LAYOUT, RECIPES[args.recipe])
    view = View(args.model, args.verbose)
    strategy = STRATEGIES[args.strategy](STATES[args.state](), Policy(), args.model, on_ask=view.ask)
    supervisor = Supervisor(line, Monitor(DETECTORS), strategy, on_symptom=view.symptom, on_action=view.action)

    supervisor.run()
    report.show(line, supervisor.incidents, args.strategy, args.state)


if __name__ == "__main__":
    main()
