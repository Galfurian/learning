"""How the questions are asked. Both strategies end with an action."""

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from declab.client import Decision, decide

from .actions import Action, CallPerson, Repair
from .policy import Policy
from .questions import SEPARATOR, which_fault, which_fault_anywhere, which_machine
from .snapshot import Snapshot
from .state import StateBuilder
from .symptoms import Symptom


@dataclass
class Ask:
    """One request to the model, kept for the trace."""

    purpose: str
    state: str
    decision: Decision


@dataclass
class Outcome:
    action: Action
    asks: list[Ask] = field(default_factory=list)


class Strategy:
    def __init__(self, state: StateBuilder, policy: Policy, model: str, on_ask: Callable[[Ask], None]) -> None:
        self.state = state
        self.policy = policy
        self.model = model
        self.on_ask = on_ask

    def decide(self, snapshot: Snapshot, symptom: Symptom) -> Outcome:
        raise NotImplementedError

    def ask(self, outcome: Outcome, purpose: str, state: str, question: dict[str, Any]) -> dict[str, Any]:
        decision = decide(state, {"answer": question}, model=self.model)
        ask = Ask(purpose, state, decision)
        outcome.asks.append(ask)
        self.on_ask(ask)
        return decision.answers["answer"]


class TwoStep(Strategy):
    """Ask which machine, then ask that machine's own question. Fall back to the
    next machine when the first one looks fine."""

    def decide(self, snapshot, symptom):
        outcome = Outcome(CallPerson("no machine explains the problem"))
        line_state = self.state.line(snapshot, symptom)
        machines = self.ask(outcome, "step 1: which machine?", line_state, which_machine(snapshot.machines))

        for name in self.policy.candidates(machines):
            machine = snapshot.machine(name)
            state = self.state.machine(snapshot, name)
            answer = self.ask(outcome, f"step 2: which fault of {name}?", state, which_fault(machine))
            fault = self.policy.fault(answer)
            if fault is not None:
                outcome.action = Repair(name, fault, answer["probabilities"][fault])
                return outcome
        return outcome


class Flat(Strategy):
    """One question over every fault of the whole line."""

    def decide(self, snapshot, symptom):
        outcome = Outcome(CallPerson("the model is not sure enough"))
        state = self.state.line(snapshot, symptom)
        answer = self.ask(outcome, "which fault, anywhere?", state, which_fault_anywhere(snapshot.machines))
        choice = self.policy.fault(answer)
        if choice is not None:
            name, fault = choice.split(SEPARATOR)
            outcome.action = Repair(name, fault, answer["probabilities"][choice])
        return outcome
