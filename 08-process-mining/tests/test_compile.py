import json
from collections import Counter

import pm4py
import pytest
from helpers import entries_of, truth_order as _truth_order

from pmlab.compile import compile_recipe, play_out
from pmlab.log import to_log
from pmlab.recipes import UNIT_ROOT, load_recipes
from pmlab.reference import to_pm4py

MAIN = (
    "reserve_pallet", "load_board", "test_board", "buffer_board", "load_covers",
    "check_covers", "assemble_gadget", "engrave_gadget", "deliver_gadget",
)
ONE_FAIL = MAIN[:6] + ("bin_covers", "reload_covers", "check_covers") + MAIN[6:]


def _gadget_language(max_len: int = 12) -> set[tuple[str, ...]]:
    return play_out(compile_recipe(load_recipes()["gadget"]), max_len=max_len)


def test_one_labelled_transition_per_operation():
    for recipe in load_recipes().values():
        net = compile_recipe(recipe)
        labels = [label for label in net.transitions.values() if label is not None]
        assert sorted(labels) == sorted(op.name for op in recipe.operations)


def test_gadget_language():
    lang = _gadget_language()
    assert MAIN in lang
    assert ONE_FAIL in lang
    # load_board and load_covers both depend only on reserve_pallet: concurrent.
    assert any(s.index("load_board") < s.index("load_covers") for s in lang)
    assert any(s.index("load_covers") < s.index("load_board") for s in lang)
    # The covers branch and the board branch overlap.
    assert any(s.index("check_covers") < s.index("test_board") for s in lang)
    for s in lang:
        assert "bin_covers" not in s or s.index("check_covers") < s.index("bin_covers")
        assert s.count("check_covers") == s.count("bin_covers") + 1
        assert s.index("assemble_gadget") > len(s) - 1 - s[::-1].index("check_covers")
        assert len(s) <= 12


def test_play_out_bounds_the_loop():
    lang = play_out(compile_recipe(load_recipes()["gadget"]))
    assert max(s.count("bin_covers") for s in lang) == 2
    assert all(len(s) <= 15 for s in lang)


def test_play_out_default_works_on_all_recipes():
    for recipe in load_recipes().values():
        assert play_out(compile_recipe(recipe))


def test_play_out_over_limit_raises():
    with pytest.raises(ValueError):
        play_out(compile_recipe(load_recipes()["gadget"]), max_len=40, limit=1000)
    with pytest.raises(ValueError):
        play_out(compile_recipe(load_recipes()["gadget"]), max_len=15, limit=100)


def test_linear_recipe_has_one_sequence():
    lang = play_out(compile_recipe(load_recipes()["brick_demo"]))
    assert lang == {("reserve_pallet", "load_bricks", "build_bricks", "check_bricks", "unbuild_bricks")}


def test_simulated_traces_fit():
    truth = json.loads((UNIT_ROOT / "data" / "logs" / "train.truth.json").read_text(encoding="utf-8"))["orders"]
    owner = {e: order for order, body in truth.items() for e in body["event_ids"]}
    recipes = load_recipes()
    # The fail loop bounded at 2: main path + 2 * (bin, reload, check).
    langs = {name: play_out(compile_recipe(r), max_len=len([o for o in r.operations if o.branch == "main"]) + 6)
             for name, r in recipes.items()}
    checked, unmapped, misfits = Counter(), [], []
    for trace in to_log(entries_of("train")):
        body = truth[_truth_order(trace, owner)]
        if body["deviations"]:
            continue
        checked[body["recipe"]] += 1
        if any(a.startswith("unmapped:") for a in trace.activities):
            unmapped.append(trace.case_id)
        if trace.activities not in langs[body["recipe"]]:
            misfits.append((trace.case_id, body["recipe"], trace.activities))
    assert set(checked) == set(recipes) and all(n > 0 for n in checked.values()), checked
    assert unmapped == []
    assert misfits == []


def test_pm4py_sound():
    for name, recipe in load_recipes().items():
        sound, _ = pm4py.analysis.check_soundness(*to_pm4py(compile_recipe(recipe)))
        assert sound, name


def test_pm4py_unsound_when_an_arc_is_missing():
    net = compile_recipe(load_recipes()["gadget"])
    net.arcs.discard(("reload_covers", "load_covers>check_covers"))
    sound, _ = pm4py.analysis.check_soundness(*to_pm4py(net))
    assert not sound
