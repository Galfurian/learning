"""Minimal checker used by exercises/*/check.py. No model is involved."""

import importlib.util
import sys
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

from .corpus import Chunk, Section
from .index import Hit


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


def fake_section(sid: str, text: str, source: str = "Demo machine", title: str = "Part") -> Section:
    return Section(sid, source, title, text)


def fake_chunk(cid: str, text: str = "some manual text", section_id: str | None = None) -> Chunk:
    return Chunk(cid, section_id or cid.rsplit("-", 1)[0], "Demo machine", "Part", text)


def fake_hits(*chunk_ids: str, scores: list[float] | None = None) -> list[Hit]:
    scores = scores or [round(0.9 - 0.1 * i, 3) for i in range(len(chunk_ids))]
    return [Hit(fake_chunk(cid), score, rank) for rank, (cid, score) in enumerate(zip(chunk_ids, scores), start=1)]


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
