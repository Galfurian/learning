"""Minimal checker used by ``exercises/*/check.py``.

A check connects to the exercise's ``mcp`` object in-process and talks to it
through the real MCP client API. No LLM is involved: the point is to verify
the MCP contract (names, schemas, results, errors) deterministically.
"""

import asyncio
import importlib.util
import sys
from collections.abc import Awaitable, Callable
from pathlib import Path
from types import ModuleType
from typing import Any

from mcp import Client


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

    def tool(self, tools: list[Any], name: str) -> Any | None:
        """Return the discovered tool called ``name``, recording a check."""
        found = next((tool for tool in tools if tool.name == name), None)
        self.ok(
            found is not None,
            f"tools/list exposes '{name}'",
            [tool.name for tool in tools],
        )
        return found


def result_value(result: Any) -> Any:
    """Return the value a tool produced, unwrapping ``{"result": ...}``."""
    data = result.structured_content
    if isinstance(data, dict) and set(data) == {"result"}:
        return data["result"]
    if data is not None:
        return data
    return "".join(getattr(block, "text", "") for block in result.content)


def error_text(result: Any) -> str:
    return "".join(getattr(block, "text", "") for block in result.content)


def _load(path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


CheckFn = Callable[[Client, Checker], Awaitable[None]]


def run_checks(
    checks: CheckFn,
    default_file: str,
    prepare: Callable[[ModuleType], None] | None = None,
) -> None:
    """Run ``checks`` against the exercise file (or a path given on the CLI).

    ``prepare`` runs on the loaded module before connecting, for example to
    register capabilities that the file only registers in its ``__main__`` block.
    """
    path = Path(sys.argv[1] if len(sys.argv) > 1 else default_file).resolve()
    print(f"Checking {path}\n")
    module = _load(path)
    if prepare is not None:
        prepare(module)

    async def main() -> Checker:
        checker = Checker()
        async with Client(module.mcp) as client:
            await checks(client, checker)
        return checker

    checker = asyncio.run(main())
    print(f"\n{checker.passed} passed, {checker.failed} failed")
    sys.exit(1 if checker.failed or not checker.passed else 0)
