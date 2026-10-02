"""Checks the line and the supervisor without any model.

The decision model is replaced by fake answers, so every rule of the
application can be tested: what the logs show, what the state contains, and
what the supervisor does with each kind of answer.
"""

import sys

import recipes
from exe08 import DETECTORS, LAYOUT
from line import FaultAt, Line, Recipe
from supervisor import strategy as strategy_module
from supervisor.actions import CallPerson, Repair
from supervisor.policy import Policy
from supervisor.snapshot import Snapshot
from supervisor.state import RawWindow, Summary
from supervisor.strategy import Flat, TwoStep
from supervisor.symptoms import WINDOW_S, Monitor, Symptom

from declab.checks import Checker, fake_choice
from declab.client import Decision

# Roughly 4 characters per token; the context of tev1 is about 2,000 tokens.
MAX_STATE_CHARS = 6000


def run_with(fault: FaultAt | None, minutes: int) -> Line:
    line = Line(LAYOUT, Recipe(parts=200, faults=[fault] if fault else []))
    line.advance(minutes * 60)
    return line


def snapshot(line: Line) -> Snapshot:
    return Snapshot(line.machines, line.logbook, max(0, line.t - WINDOW_S), line.t)


def check_line(check: Checker) -> None:
    healthy = Summary().line(snapshot(run_with(None, 30)), Symptom(0, "-"))
    check.ok(
        "above nominal" not in healthy and "below nominal" not in healthy,
        "a healthy line: every signal within nominal",
        healthy,
    )

    for name, cls in LAYOUT:
        for fault in cls.faults:
            line = run_with(FaultAt("0810", name, fault.name()), 30)
            summary = Summary().machine(snapshot(line), name)
            raw = RawWindow().machine(snapshot(line), name)
            line_state = Summary().line(snapshot(line), Symptom(line.t, "-"))
            check.ok(
                "above nominal" in summary or "below nominal" in summary,
                f"{name} {fault.name()}: some signal of {name} leaves its nominal range",
                summary,
            )
            leaked = [text for text in (summary, raw, line_state) if fault.name() in text.lower()]
            check.ok(not leaked, f"{name} {fault.name()}: no state names the fault", leaked)
            check.ok(len(line_state) < MAX_STATE_CHARS, f"{name} {fault.name()}: the line state fits the context", len(line_state))

            line.machine(name).repair(fault.name(), line.t)
            check.ok(not line.active_faults(), f"{name} {fault.name()}: its remedy removes it", line.active_faults())


def check_quiet_run(check: Checker) -> None:
    line = Line(LAYOUT, recipes.QUIET)
    monitor = Monitor(DETECTORS)
    symptoms = []
    while not line.done:
        line.advance(60)
        symptom = monitor.check(line.logbook, line.t)
        if symptom:
            symptoms.append(symptom.text)
    rejected = [part.id for part in line.finished if part.status == "rejected"]
    check.ok(not symptoms and not rejected, "QUIET recipe: no symptom, no reject", symptoms or rejected)


def fake_model(answers: dict[str, dict[str, float]]):
    """A stand-in for ``decide``: answers by the first word of the state."""

    def decide(state, questions, model):
        key = state.split()[0] if not state.startswith("Problem") else "line"
        return Decision({"answer": fake_choice(answers[key])}, {}, 0.0, {})

    return decide


def check_policy(check: Checker) -> None:
    line = run_with(FaultAt("0810", "Q1", "gauge_drift"), 30)
    view = snapshot(line)
    symptom = Symptom(line.t, "3 of the last 10 parts were rejected at final inspection.")

    def decide(strategy_class, answers):
        strategy_module.decide = fake_model(answers)
        strategy = strategy_class(Summary(), Policy(), "fake", on_ask=lambda ask: None)
        return strategy.decide(view, symptom)

    outcome = decide(TwoStep, {
        "line": {"F1": 0.02, "C1": 0.03, "M1": 0.60, "Q1": 0.35},
        "M1": {"tool_wear": 0.05, "wrong_offset": 0.05, "coolant_low": 0.05, "none": 0.85},
        "Q1": {"dirty_lens": 0.05, "gauge_drift": 0.85, "none": 0.10},
    })
    check.ok(
        outcome.action == Repair("Q1", "gauge_drift", 0.85) and len(outcome.asks) == 3,
        "two-step: the first machine looks fine -> try the second one, repair there",
        outcome.action,
    )

    outcome = decide(TwoStep, {
        "line": {"F1": 0.02, "C1": 0.03, "M1": 0.60, "Q1": 0.35},
        "M1": {"tool_wear": 0.30, "wrong_offset": 0.40, "coolant_low": 0.10, "none": 0.20},
        "Q1": {"dirty_lens": 0.05, "gauge_drift": 0.15, "none": 0.80},
    })
    check.ok(isinstance(outcome.action, CallPerson), "two-step: nobody is sure -> call a technician", outcome.action)

    outcome = decide(TwoStep, {
        "line": {"F1": 0.01, "C1": 0.01, "M1": 0.97, "Q1": 0.01},
        "M1": {"tool_wear": 0.05, "wrong_offset": 0.05, "coolant_low": 0.05, "none": 0.85},
    })
    check.ok(
        isinstance(outcome.action, CallPerson) and len(outcome.asks) == 2,
        "two-step: machines below min_machine_p are never asked",
        [ask.purpose for ask in outcome.asks],
    )

    flat_answers = {key: 0.01 for key in ["F1/misfeed", "F1/empty_hopper", "C1/jam", "C1/belt_slip",
                                          "M1/tool_wear", "M1/wrong_offset", "M1/coolant_low",
                                          "Q1/dirty_lens", "none"]}
    flat_answers["Q1/gauge_drift"] = 0.91
    outcome = decide(Flat, {"line": flat_answers})
    check.ok(outcome.action == Repair("Q1", "gauge_drift", 0.91), "flat: a sure answer -> repair", outcome.action)


def main() -> None:
    check = Checker()
    print("The line\n")
    check_line(check)
    check_quiet_run(check)
    print("\nThe supervisor, with fake answers\n")
    original = strategy_module.decide
    try:
        check_policy(check)
    finally:
        strategy_module.decide = original
    print(f"\n{check.passed} passed, {check.failed} failed")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
