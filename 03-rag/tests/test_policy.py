from raglab.evalset import Question
from raglab.generation import answer_ok
from raglab.runners import threshold_table


def test_answer_ok():
    q = Question("q", "x", frozenset({"a"}), "c", "", ("15", "22 °C"))
    assert answer_ok("Between 15 and 22 °C. [a-1]", q)
    assert not answer_ok("Between 15 and 25 °C.", q)
    assert not answer_ok("Not in the manuals.", q)
    none = Question("n", "x", frozenset(), "no-answer", "", ())
    assert answer_ok("Not in the manuals.", none) and not answer_ok("Two years.", none)


def test_threshold_table_counts_errors_and_cost():
    # (top-1 score, answerable?)
    top1 = [(0.30, True), (0.60, True), (0.45, False)]
    rows = {round(t, 2): (miss, false, cost) for t, miss, false, cost in threshold_table(top1, 5.0, 1.0)}
    assert rows[0.0] == (0, 1, 1.0)          # accept everything: one no-answer passes
    assert rows[0.3] == (0, 1, 1.0)
    assert rows[0.45] == (1, 1, 6.0)         # 0.45 itself passes: ">=" accepts it
    assert rows[0.6] == (1, 0, 5.0)          # refuse below 0.6: one answerable missed


def test_threshold_equal_to_a_score_accepts_that_question():
    # A rounded candidate (0.349) would be above 0.3487 and refuse it.
    rows = threshold_table([(0.3487, True), (0.5576, False)], 5.0, 1.0)
    assert (0.3487, 0, 1, 1.0) in rows
    assert (0.5576, 1, 1, 6.0) in rows
