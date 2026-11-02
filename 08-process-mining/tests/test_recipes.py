import re
import subprocess

from pmlab.recipes import UNIT_ROOT, load_recipes

# The pattern of unit 07, with node ids narrowed to the OPC-UA shape (ruling R7).
# Built from fragments so that this file does not match it.
FORBIDDEN = re.compile(
    r"(?:\bn" + r"s=\d+;|opc" + r"\.tcp|https?:" + "//|" + r"\b(?:tok" + r"en|pass" + r"word|sec" + r"ret|api[_-]?" + r"key)\b\s*[:=]\s*\S|\b\d{1,3}(?:\.\d{1,3}){3}\b)",
    re.I,
)
ACTIVITIES = {"mission", "bay_stay", "check_passed", "check_failed", "test_result",
              "operation_started", "operation_done", "program_started", "program_ended"}
# Ruling R6: same missions in both; told apart by context, not by evidence.
EXEMPT = {frozenset({"load_covers", "reload_covers"})}
RESOURCES = {"robot_a", "robot_b", "tester", "qc_station", "assembly_cell", "mill_cell", "conveyor", "storage"}
BAYS = {"load", "tester", "qc", "assembly", "mill"}


def main_ops(recipe):
    return [op.name for op in recipe.operations if op.branch == "main"]


def test_recipes_shape():
    recipes = load_recipes()
    assert set(recipes) == {"gadget", "parts_test", "brick_demo"}
    for recipe in recipes.values():
        names = {op.name for op in recipe.operations}
        assert len(names) == len(recipe.operations)
        for op in recipe.operations:
            assert set(op.depends) <= names
            assert op.branch in {"main", "fail"}
            assert 0 < op.min_s <= op.nominal_s
            assert set(op.resources) <= RESOURCES
            assert op.evidence
            for step in op.evidence:
                assert step.resource in RESOURCES
                assert step.activity in ACTIVITIES
                if "bay" in step.attrs:
                    assert step.attrs["bay"] in BAYS
    fail = {op.name for op in recipes["gadget"].operations if op.branch == "fail"}
    assert fail == {"bin_covers", "reload_covers"}


def test_shared_prefix():
    recipes = load_recipes()
    gadget, parts, bricks = (main_ops(recipes[n]) for n in ("gadget", "parts_test", "brick_demo"))
    assert gadget[:4] == parts[:4]
    assert gadget[4] != parts[4]
    assert bricks[0] == gadget[0]
    assert bricks[1] != gadget[1]


def test_same_name_same_evidence():
    seen = {}
    for recipe in load_recipes().values():
        for op in recipe.operations:
            key = (op.evidence, op.resources, op.nominal_s, op.min_s)
            assert seen.setdefault(op.name, key) == key, op.name


def ambiguous(a, b):
    """Step a matches every event of step b, or the other way round."""
    if (a.activity, a.resource) != (b.activity, b.resource):
        return False
    return a.attrs.items() <= b.attrs.items() or b.attrs.items() <= a.attrs.items()


def test_each_operation_has_a_unique_evidence_step():
    by_name = {}
    for recipe in load_recipes().values():
        for op in recipe.operations:
            by_name[op.name] = op
    for name, op in by_name.items():
        others = [
            o for n, o in by_name.items()
            if n != name and frozenset({n, name}) not in EXEMPT
        ]
        assert any(
            not any(ambiguous(step, s) for o in others for s in o.evidence)
            for step in op.evidence
        ), name


def test_no_real_names():
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "."],
        cwd=UNIT_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    assert listed
    for name in listed:
        path = UNIT_ROOT / name
        if path.suffix in {".py", ".yaml", ".yml", ".json", ".jsonl", ".md", ".toml"} and path.name != "uv.lock":
            for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
                assert not FORBIDDEN.search(line), f"{name}:{line_no}"
