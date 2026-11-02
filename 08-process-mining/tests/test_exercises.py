"""The exercises: each check passes on its solution, each stub asks for its TODO.

The scripts run as subprocesses with the unit's interpreter, from the unit folder.
"""

import subprocess
import sys

import pytest

from pmlab.recipes import UNIT_ROOT

EXERCISES = UNIT_ROOT / "exercises"
TASKS = {
    "01": "exe01-event-log",
    "02": "exe02-abstraction",
    "03": "exe03-dfg",
    "04": "exe04-alpha",
    "05": "exe05-recipe-net",
    "06": "exe06-token-replay",
    "07": "exe07-alignments",
    "08": "exe08-performance",
    "09": "exe09-monitoring",
    "10": "exe10-ocel",
}


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, *args], cwd=UNIT_ROOT, capture_output=True, text=True, timeout=300)


def test_every_exercise_folder_exists():
    names = sorted(p.name for p in EXERCISES.iterdir() if p.is_dir() and p.name.startswith("exe"))
    assert names == ["exe00-demo", *TASKS.values(), "exe11-benchmark", "exe12-generator"]
    for n in TASKS:
        assert (EXERCISES / "solutions" / f"exe{n}.py").exists()


@pytest.mark.parametrize("n", sorted(TASKS))
def test_solution_passes_check(n):
    folder = EXERCISES / TASKS[n]
    out = _run(str(folder / "check.py"), str(EXERCISES / "solutions" / f"exe{n}.py"))
    assert out.returncode == 0, out.stdout + out.stderr
    assert "FAIL" not in out.stdout
    assert " 0 failed" in out.stdout


@pytest.mark.parametrize("n", sorted(TASKS))
def test_stub_asks_for_the_todo(n):
    stub = EXERCISES / TASKS[n] / f"exe{n}.py"
    if "NotImplementedError" not in stub.read_text(encoding="utf-8"):
        pytest.skip("the exercise is solved in this working copy")
    run = _run(str(stub))
    assert run.returncode == 1, run.stdout + run.stderr
    assert "TODO" in run.stdout and "not implemented yet" in run.stdout
    check = _run(str(EXERCISES / TASKS[n] / "check.py"))
    assert check.returncode == 1 and "FAIL" in check.stdout


@pytest.mark.parametrize("n, log, line", [
    ("02", "train", "same entries as the reference: True"),
    ("09", "train", "same candidates as the reference on ref-order and on train: True"),
])
def test_solution_equals_the_reference_on_a_log(n, log, line):
    out = _run(str(EXERCISES / "solutions" / f"exe{n}.py"), "--log", log)
    assert out.returncode == 0, out.stdout + out.stderr
    assert line in " ".join(out.stdout.split()), out.stdout


def test_demo_runs_without_a_model():
    out = _run(str(EXERCISES / "exe00-demo" / "exe00.py"), "--no-model")
    assert out.returncode == 0, out.stdout + out.stderr
    assert "engrave_gadget" in out.stdout and "unusual" in out.stdout


def test_generator_exercise_starts_from_the_unit_prompt():
    import importlib.util

    from pmlab.answer import SYSTEM_PROMPT, messages
    spec = importlib.util.spec_from_file_location("exe12", EXERCISES / "exe12-generator" / "exe12.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if module.SYSTEM_PROMPT != SYSTEM_PROMPT:
        pytest.skip("the prompt is changed in this working copy")
    assert messages("q", ["[e1] x (derived)"], system="mine")[0]["content"] == "mine"


def test_generator_exercise_refuses_an_empty_prompt(monkeypatch, capsys):
    from pmlab.runners import run_prompt_experiment
    monkeypatch.setattr(sys, "argv", ["exe12.py"])
    with pytest.raises(SystemExit) as stop:
        run_prompt_experiment("  ", "exe12.py")
    assert stop.value.code == 1
    assert "TODO" in capsys.readouterr().out
