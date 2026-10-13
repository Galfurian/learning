"""Copied from unit 05 (05-knowledge-graphs/src/kglab/checks.py), trimmed to what unit 07 uses."""

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any



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

    def calls(self, function: Callable[..., Any], *args: Any) -> tuple[bool, Any]:
        """Call ``function``; NotImplementedError becomes one failed check."""
        try:
            return True, function(*args)
        except NotImplementedError:
            self.ok(False, f"{function.__name__}() is implemented")
            return False, None


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_checks(checks: Callable[[ModuleType, Checker], None], default_file: str) -> None:
    path = Path(sys.argv[1] if len(sys.argv) > 1 else default_file).resolve()
    print(f"Checking {path}\n")
    checker = Checker()
    checks(_load(path), checker)
    print(f"\n{checker.passed} passed, {checker.failed} failed")
    sys.exit(1 if checker.failed or not checker.passed else 0)
