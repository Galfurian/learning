from evlab.answer import Answer
from evlab.benchmark import expectation, score
from evlab.chain import Chain
from evlab.records import Event


def ev(i):
    return Event(f"e{i}", "check_failed", "qc_station", 1.0, 1.0, 1.0, ("c1",), "r", "1", "derived", 7, "p7#1")


CHAIN = Chain("p7#1", 7, [ev(1)], [], 0)


def ans(text, cited=("e1",), refused=False):
    return Answer(text, list(cited), [], refused, 0.0)


def test_a_wrong_answer_with_the_right_id_fails():
    q = {"id": "q", "type": "what-happened", "gold_case": "p7#1", "gold_event_ids": ["e1"], "abstain": False,
         "expect": {"all": ["failed"], "none": ["passed"]}}
    assert score(q, CHAIN, ans("Pallet 7 passed and nothing happened [e1].")).stage == "GENERATION"
    assert score(q, CHAIN, ans("The check failed [e1].")).stage == "NONE"


def test_an_abstention_needs_its_evidence():
    q = {"id": "q", "type": "abstain", "gold_case": None, "gold_event_ids": ["e9"], "abstain": True}
    row = score(q, Chain("resource", None, [], [], 0), ans("Not in the recording.", cited=(), refused=True))
    assert row.stage == "SELECTION"


def test_expectation():
    assert expectation({"expect": {"all": ["A"], "none": ["b"]}}, "a and c") == []
    assert expectation({"expect": {"all": ["x"], "none": ["c"]}}, "a and c") == ["missing 'x'", "says 'c'"]


def test_synonym_groups():
    assert expectation({"expect": {"all": [["left", "released"], "523"]}}, "It was released at t=523 s.") == []
