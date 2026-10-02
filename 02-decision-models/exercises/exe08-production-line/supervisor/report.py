"""After the run: what the supervisor did, against what was really broken."""

from line import Line, hhmm
from rich.table import Table

from declab import ui

from .actions import CallPerson, Repair
from .supervisor import Incident


def verdict(incident: Incident) -> str:
    action = incident.outcome.action
    if isinstance(action, CallPerson):
        return "~ technician called"
    if (action.machine, action.fault) in incident.truth:
        return "✓ right repair"
    return "✗ wrong repair"


def show(line: Line, incidents: list[Incident], strategy: str, state: str) -> None:
    table = Table(title=f"Report · {strategy} · {state}", show_header=True, header_style="bold", expand=True)
    for column in ["#", "Time", "Really broken", "Action", "Verdict", "Calls", "Model s"]:
        table.add_column(column)
    calls = seconds = 0.0
    for number, incident in enumerate(incidents, start=1):
        asks = incident.outcome.asks
        spent = sum(ask.decision.seconds for ask in asks)
        calls += len(asks)
        seconds += spent
        action = incident.outcome.action
        table.add_row(
            str(number),
            hhmm(incident.symptom.t),
            ", ".join(f"{machine}: {fault}" for machine, fault in incident.truth) or "-",
            f"{action.machine}: {action.fault}" if isinstance(action, Repair) else "technician",
            verdict(incident),
            str(len(asks)),
            f"{spent:.1f}",
        )
    ui.console.print(table)
    rejected = sum(part.status == "rejected" for part in line.finished)
    ui.console.print(
        f"{len(line.finished)} parts, {rejected} rejected · finished at {hhmm(line.t)} · "
        f"{int(calls)} model calls, {seconds:.1f}s · still broken at the end: {line.active_faults() or 'nothing'}"
    )
