import importlib.util
import sys
from pathlib import Path

import pytest

from raglab import runners
from raglab.client import OllamaError

SOLUTION = Path(__file__).resolve().parents[1] / "exercises" / "solutions" / "exe07.py"


def exe07():
    spec = importlib.util.spec_from_file_location("exe07_solution", SOLUTION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_hybrid_runs_a_free_question(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["exe07.py", "--fake-embed", "--question", "What is PN-77A?"])
    solution = exe07()
    runners.run_hybrid(solution.keyword_search, solution.fuse, str(SOLUTION))
    out = capsys.readouterr().out
    assert "QUESTION 1/1" in out and "lx40" in out


def test_hybrid_reports_ollama_errors_after_a_cached_index(monkeypatch):
    def fail(*args, **kwargs):
        raise OllamaError("cannot reach Ollama. Is `ollama serve` running?")

    monkeypatch.setattr(sys, "argv", ["exe07.py", "--fake-embed", "--eval"])
    monkeypatch.setattr(runners, "run_search", fail)
    solution = exe07()
    with pytest.raises(SystemExit) as info:
        runners.run_hybrid(solution.keyword_search, solution.fuse, str(SOLUTION))
    assert info.value.code == 1
