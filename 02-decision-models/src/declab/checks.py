"""Minimal checker used by ``exercises/*/check.py``.

A check imports the exercise file and calls its parts directly. No model is
involved: ``build_state`` and ``act`` are ordinary functions, so they can be
tested with fake answers that have exactly the shape Ollama returns.
"""

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

from .questions import entropy_confidence, problems


class Checker:
    def __init__(self) -> None:
        self.passed = 0
        self.failed = 0

    def ok(self, condition: bool, message: str, detail: Any = None) -> bool:
        if condition:
            self.passed += 1
            print(f"  PASS  {message}")
        else:
            self.failed += 1
            print(f"  FAIL  {message}")
            if detail is not None:
                print(f"        got: {detail}")
        return condition

    def question(self, questions: Any, name: str, kind: str) -> dict[str, Any] | None:
        """Return question ``name`` if it exists with type ``kind``, recording a check."""
        found = questions.get(name) if isinstance(questions, dict) else None
        self.ok(
            isinstance(found, dict) and found.get("type") == kind,
            f"QUESTIONS has a '{kind}' question named '{name}'",
            found if found is not None else list(questions or {}),
        )
        return found if isinstance(found, dict) and found.get("type") == kind else None

    def valid(self, state: Any, questions: Any) -> bool:
        found = problems(state, questions)
        return self.ok(not found, "the request is well formed (Ollama would accept it)", found)

    def calls(self, function: Callable[..., Any], *args: Any) -> tuple[bool, Any]:
        """Call ``function``; a NotImplementedError becomes one failed check."""
        try:
            return True, function(*args)
        except NotImplementedError:
            self.ok(False, f"{function.__name__}() is implemented")
            return False, None


def fake_noul(probability: float) -> dict[str, Any]:
    return {"type": "noul", "noul": probability}


def fake_choice(probabilities: dict[str, float]) -> dict[str, Any]:
    return {
        "type": "choice",
        "choice": max(probabilities, key=probabilities.get),
        "probabilities": probabilities,
        "confidence": entropy_confidence(probabilities),
    }


def fake_score(probabilities: list[float], criteria: list[str]) -> dict[str, Any]:
    by_index = {str(index): p for index, p in enumerate(probabilities)}
    return {
        "type": "score",
        "score": sum(index * p for index, p in enumerate(probabilities)),
        "legend": {str(index): label for index, label in enumerate(criteria)},
        "probabilities": by_index,
        "confidence": entropy_confidence(by_index),
    }


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_checks(checks: Callable[[ModuleType, Checker], None], default_file: str) -> None:
    """Run ``checks`` against the exercise file (or a path given on the CLI)."""
    path = Path(sys.argv[1] if len(sys.argv) > 1 else default_file).resolve()
    print(f"Checking {path}\n")
    module = _load(path)
    checker = Checker()
    checks(module, checker)
    print(f"\n{checker.passed} passed, {checker.failed} failed")
    sys.exit(1 if checker.failed or not checker.passed else 0)
