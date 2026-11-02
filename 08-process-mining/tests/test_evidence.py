from pmlab.evidence import Mined, evidence_lines, mine, pipeline
from pmlab.log import Entry, Trace


def _joined(name, order, now):
    return "\n".join(evidence_lines(pipeline(name), order, now))


def test_pipeline_cached_and_named():
    m = pipeline("ref-order")
    assert pipeline("ref-order") is m
    assert list(m.traces) == ["order:1"]
    assert set(m.nets) == {"gadget", "parts_test", "brick_demo"}
    assert m.stats is pipeline("train").stats     # the baseline is always the train log


def test_evidence_ref_stuck():
    m = pipeline("ref-stuck")
    lines = evidence_lines(m, "order:1", 1400)
    text = "\n".join(lines)
    p95 = m.stats["engrave_gadget"].p95
    (line,) = [x for x in lines if "engrave_gadget" in x and "open" in x]
    assert "482" in line and "unusual" in line and f"{p95:.0f}" in line and "nominal 150" in line
    assert "[e54" in line and line.endswith("(derived)")
    assert "fail branch of the recipe: conformant" in text
    assert "does not show why" in text
    assert all(x.endswith(")") for x in lines)


def test_evidence_ref_order():
    lines = evidence_lines(pipeline("ref-order"), "order:1", 1118)
    (line,) = [x for x in lines if "engrave_gadget" in x and "open" in x]
    assert "running" in line and "unusual" not in line and "200" in line
    (recipe,) = [x for x in lines if "recipe gadget" in x and "only" in x]
    assert recipe.startswith("[e17, e18, e19, e29]") and recipe.endswith("(derived)")


def test_undecided_recipe_is_inferred():
    f = mine(pipeline("ref-prefix"), "order:1", 250)
    assert f.recipes == ["gadget", "parts_test"]
    (line,) = [x for x in f.lines if "parts_test" in x]
    assert line.endswith("(inferred)") and "check_covers" in line and "mill_part" in line
    assert line.startswith("[e1, e2, e3, e5]")
    assert f.moves == []


def test_skipped_check_is_a_model_move():
    f = mine(pipeline("ref-skip-check"), "order:1", 1118)
    assert f.recipes == []
    assert f.moves == [("model", "check_covers")]
    assert any("check_covers" in x and "skipped" in x for x in f.lines)


def test_finished_train_order_has_complete_alignment():
    m = pipeline("train")
    f = mine(m, "order:33", 1e9)
    assert f.moves == [("model", "buffer_board")]
    assert f.open == []


def test_fail_frequency_over_train():
    m = pipeline("train")
    checks, fails = m.fail_rate
    assert 0 < fails < checks
    text = "\n".join(evidence_lines(m, "order:3", 1e9))
    assert f"{fails} of {checks}" in text


def test_unknown_order_and_time_before_start():
    assert "not in the log" in _joined("ref-order", "order:9", 500)
    assert "no entry before" in _joined("ref-order", "order:1", 10)


def test_unmapped_gets_a_coverage_line():
    base = pipeline("ref-order")
    trace = base.traces["order:1"]
    extra = Entry("order:1", "unmapped:check_passed", "complete", 300.0, "qc_station", ("order:1",), ("e999",),
                  "inferred")
    entries = sorted([*trace.entries, extra], key=lambda e: e.time)
    m = Mined("synthetic", base.recipes, {"order:1": Trace("order:1", entries)}, base.nets, base.stats,
              base.fail_rate)
    f = mine(m, "order:1", 1118)
    assert f.moves == []                              # conformance ignores it
    (line,) = [x for x in f.lines if "unmapped:check_passed" in x]
    assert line.startswith("[e999]") and "ignores" in line and line.endswith("(coverage)")
