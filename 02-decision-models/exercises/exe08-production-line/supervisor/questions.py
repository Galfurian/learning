"""The questions. Every word of an option comes from the machine classes."""

from typing import Any

from line import Machine

NONE = "none"
NONE_DESCRIPTION = "None of these faults: every signal is within its nominal range."
SEPARATOR = "/"


def which_machine(machines: list[Machine]) -> dict[str, Any]:
    """Step 1: which machine most likely causes the problem."""
    return {
        "type": "choice",
        "instructions": "A problem was detected on the production line. Which machine most likely causes it?",
        "criteria": {machine.name: f"The {machine.kind}. {machine.description}" for machine in machines},
    }


def which_fault(machine: Machine) -> dict[str, Any]:
    """Step 2: which fault of this machine explains its signals."""
    criteria = {fault.name(): fault.description for fault in machine.faults}
    criteria[NONE] = NONE_DESCRIPTION
    return {
        "type": "choice",
        "instructions": (
            f"The signals of this {machine.kind} are listed with their nominal ranges. "
            "Which fault best explains them?"
        ),
        "criteria": criteria,
    }


def which_fault_anywhere(machines: list[Machine]) -> dict[str, Any]:
    """The flat alternative: one question over every fault of every machine."""
    criteria = {
        f"{machine.name}{SEPARATOR}{fault.name()}": f"{machine.name} ({machine.kind}): {fault.description}"
        for machine in machines
        for fault in machine.faults
    }
    criteria[NONE] = NONE_DESCRIPTION
    return {
        "type": "choice",
        "instructions": (
            "A problem was detected on the production line. The signals of every machine are "
            "listed with their nominal ranges. Which fault best explains them?"
        ),
        "criteria": criteria,
    }
