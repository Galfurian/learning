"""Command line shared by every ``exercises/*/exeNN.py`` file.

An exercise file has three parts, and this module runs them in order for
every case:

1. ``build_state(case)``  APP code: turn application data into the state;
2. ``QUESTIONS``          sent with the state to the decision MODEL;
3. ``act(case, answers)`` APP code: do something with the answers.

The model only takes part in step 2.
"""

import argparse
import json
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from . import ui
from .client import DEFAULT_MODEL, DecisionError, decide, decide_each, request_body
from .questions import problems

BuildState = Callable[[Any], Any]
Act = Callable[[Any, dict[str, Any]], Any]


def _identity(case: Any) -> Any:
    return case


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run this exercise: the decision model answers QUESTIONS about every case."
    )
    parser.add_argument(
        "--state",
        help="Send this state instead of the CASES (JSON is parsed, anything else is text). "
        "It skips build_state(), and act() when the file has a build_state().",
    )
    parser.add_argument(
        "--case",
        type=int,
        help="Run only case N of CASES (1-based).",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Any decision model installed locally (capability 'decision').",
    )
    parser.add_argument(
        "--separately",
        action="store_true",
        help="Send every question in its own request instead of all in one request.",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--verbose",
        action="store_true",
        help="Show the full HTTP request and response of every call.",
    )
    mode.add_argument(
        "--inspect",
        action="store_true",
        help="Show the requests the APP would send, without calling the model.",
    )
    return parser.parse_args()


def _parse_case(text: str) -> Any:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _select(cases: Sequence[Any], args: argparse.Namespace) -> list[Any]:
    if args.state is not None:
        return [_parse_case(args.state)]
    if args.case is not None:
        if not 1 <= args.case <= len(cases):
            raise SystemExit(f"--case must be between 1 and {len(cases)}")
        return [cases[args.case - 1]]
    return list(cases)


def run(
    questions: dict[str, Any],
    cases: Sequence[Any],
    file: str,
    *,
    build_state: BuildState = _identity,
    act: Act | None = None,
    separately: bool = False,
) -> None:
    """Entry point of an exercise file: ``run(QUESTIONS, CASES, __file__, ...)``.

    By default all the questions about one case go in one request (``decide``).
    ``separately=True`` or ``--separately`` sends one request per question
    (``decide_each``), so no question sees another one; EXE06 compares the two.
    """
    args = parse_args()
    together = not (separately or args.separately)
    label = Path(file).name
    selected = _select(cases, args)
    # --state is the state itself: there is no application record behind it.
    raw_state = args.state is not None
    if raw_state and build_state is not _identity:
        act = None
        ui.show_note("--state skips build_state() and act(): there is no application record.")

    if args.verbose:
        ui.show_actors(args.model, label)

    started = time.perf_counter()
    rows: list[tuple[str, str, str, float]] = []
    tokens = 0

    for index, case in enumerate(selected, start=1):
        ui.show_case_header(index, len(selected))

        try:
            state = case if raw_state else build_state(case)
        except NotImplementedError:
            ui.show_todo("build_state(case)", "Until it returns a state, there is nothing to ask.")
            return
        ui.show_state(state)

        bodies = (
            [request_body(args.model, state, questions)]
            if together or not isinstance(questions, dict) or not questions
            else [request_body(args.model, state, {name: q}) for name, q in questions.items()]
        )

        if args.inspect:
            for body in bodies:
                ui.show_request(body)
            ui.show_problems(problems(state, questions))
            continue

        def trace(body: dict[str, Any], one: Any) -> None:
            if args.verbose:
                ui.show_request(body)
                ui.show_response(one.raw)

        try:
            if len(bodies) == 1:
                decision = decide(state, questions, model=args.model)
                trace(bodies[0], decision)
            else:
                decision = decide_each(state, questions, model=args.model, on_request=trace)
        except DecisionError as exc:
            ui.show_error(str(exc))
            return
        ui.show_decision(
            decision.answers, args.model, decision.seconds, decision.usage, requests=len(bodies)
        )
        tokens += decision.usage.get("input_tokens", 0)

        action = "-"
        if act is not None:
            try:
                action = act(case, decision.answers)
                ui.show_action(action)
            except NotImplementedError:
                ui.show_todo("act(case, answers)", "The model answered, but your application does nothing yet.")
                action = "(not implemented)"

        rows.append(
            (
                ui.short_state(state),
                ui.short_decision(decision.answers),
                str(action),
                decision.seconds,
            )
        )

    if rows:
        ui.show_summary(rows, time.perf_counter() - started, tokens)
