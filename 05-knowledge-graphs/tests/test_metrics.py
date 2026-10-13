from kglab.metrics import AMBIGUOUS, answer_scores, path_correct, resolution_counts, triple_scores


def test_triple_scores_per_relation():
    gold = {("a", "r1", "b"), ("a", "r2", "c"), ("d", "r1", "e")}
    pred = {("a", "r1", "b"), ("a", "r2", "x")}
    s = triple_scores(pred, gold)
    assert (s["all"].tp, s["all"].predicted, s["all"].gold) == (1, 2, 3)
    assert s["r1"].precision == 1.0 and s["r1"].recall == 0.5
    assert s["r2"].f1 == 0.0


def test_path_and_answers():
    assert path_correct(["a", "^b"], ("a", "^b"))
    assert not path_correct(["a", "b"], ["a", "^b"])
    assert path_correct(None, None) and not path_correct(None, ["a"])
    s = answer_scores(["x", "y"], ["y", "z"])
    assert (s.precision, s.recall) == (0.5, 0.5)


def test_resolution_counts():
    c = resolution_counts([("n1", "n1"), ("n2", "n1"), (None, "n1"), (AMBIGUOUS, AMBIGUOUS), ("n1", AMBIGUOUS)])
    assert (c.right, c.wrong, c.unresolved, c.ambiguous_ok, c.ambiguous_missed) == (1, 1, 1, 1, 1)
    assert c.accuracy == 0.4
