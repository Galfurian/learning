"""Rich rendering for the demo. Not part of the decision logic."""

from line import hhmm

from declab import ui

from .strategy import Ask, Outcome
from .symptoms import Symptom


class View:
    def __init__(self, model: str, verbose: bool) -> None:
        self.model = model
        self.verbose = verbose

    def symptom(self, number: int, symptom: Symptom) -> None:
        ui.console.rule(f"[bold]INCIDENT {number} · {hhmm(symptom.t)}")
        ui.console.print(f"[bold red]Symptom (detected by code):[/bold red] {symptom.text}")

    def ask(self, ask: Ask) -> None:
        ui.console.print(f"[bold]{ask.purpose}[/bold]")
        if self.verbose:
            ui.show_state(ask.state)
        ui.show_decision(ask.decision.answers, self.model, ask.decision.seconds, ask.decision.usage)

    def action(self, outcome: Outcome) -> None:
        ui.show_action(outcome.action.text())
