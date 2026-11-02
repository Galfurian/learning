from pmlab.answer import REFUSAL, SYSTEM_PROMPT, cited_ids, judge
from pmlab.benchmark import DEV, HOLDOUT, expectation, load_questions, run, score, select, summary
from pmlab.evidence import mine, pipeline


def _q(**kw):
    q = {"id": "q", "type": "stopped", "log": "ref-stuck", "order": "order:1", "now": 1400,
         "gold_recipe": "gadget", "gold_open": [["engrave_gadget", "unusual"]], "gold_moves": [],
         "gold_ids": ["e54"], "abstain": False, "expect": {"all": [["unusual"]], "none": [["running"]]}}
    return {**q, **kw}


def _finding():
    return mine(pipeline("ref-stuck"), "order:1", 1400)


def test_prompt_rules():
    assert "probably" in SYSTEM_PROMPT and "Unusual is a comparison with the baseline" in SYSTEM_PROMPT
    assert REFUSAL in SYSTEM_PROMPT


def test_cited_ids():
    assert cited_ids("It is open [e54, e55] and [e54]; see [order:1].") == ["e54", "e55"]


def test_select_parses_order_and_time():
    m = pipeline("train")
    assert select("Where is order 2 at t=900 s?", m, 50.0) == ("order:2", 900.0)
    assert select("Where is order:12 now?", m, 50.0) == ("order:12", 50.0)
    assert select("Which recipe is it?", pipeline("ref-order"), 1118) == ("order:1", 1118)
    assert select("Which recipe is it?", m, 5.0) == (None, 5.0)


def test_stages():
    f = _finding()
    lines = f.lines
    good = judge("engrave_gadget is open for 482 s, unusual over p95 [e54].", lines)
    assert score(_q(), "order:1", 1400, f, good).stage == "NONE"
    assert score(_q(), "order:2", 1400, f, good).stage == "SELECTION"
    assert score(_q(now=1118), "order:1", 1400, f, good).stage == "SELECTION"
    assert score(_q(gold_open=[["engrave_gadget", "running"]]), "order:1", 1400, f, good).stage == "MINING"
    assert score(_q(gold_moves=[["model", "check_covers"]]), "order:1", 1400, f, good).stage == "MINING"
    bad = judge("engrave_gadget is running normally [e54].", lines)
    assert score(_q(), "order:1", 1400, f, bad).stage == "GENERATION"
    unknown = judge("engrave_gadget is unusual [e7777].", lines)
    assert score(_q(), "order:1", 1400, f, unknown).stage == "GENERATION"


def test_abstention():
    f = mine(pipeline("train"), "order:250", 1000)
    q = _q(log="train", order="order:250", now=1000, gold_recipe=[], gold_open=[], gold_ids=[], abstain=True,
           expect={"all": [], "none": []})
    assert score(q, "order:250", 1000, f, judge(REFUSAL, f.lines)).stage == "NONE"
    assert score(q, "order:250", 1000, f, judge("It is at load_board [e1].", f.lines)).stage == "GENERATION"


def test_expectation_synonyms():
    assert expectation({"expect": {"all": [["left", "released"], ["523"]], "none": []}}, "released at 523 s") == []
    assert expectation({"expect": {"all": [["x"]], "none": [["c"]]}}, "a and c") == ["missing ['x']", "says ['c']"]


def test_mining_stage_on_gold():
    """With a generator that returns the gold answer, every dev question is right."""
    questions = load_questions(DEV)
    rows = run(questions, generator=lambda q, lines: judge(q["gold_answer"], lines))
    assert [(r.id, r.stage, r.notes) for r in rows] == [(q["id"], "NONE", []) for q in questions]
    assert summary(rows)["right"] == len(questions) == 12


def test_holdout_gold_scores_none():
    questions = load_questions(HOLDOUT)
    rows = run(questions, generator=lambda q, lines: judge(q["gold_answer"], lines))
    assert [(r.id, r.stage, r.notes) for r in rows] == [(q["id"], "NONE", []) for q in questions]


def _dev(qid):
    return next(q for q in load_questions(DEV) if q["id"] == qid)


def _score_text(q, text):
    f = mine(pipeline(q["log"]), q["order"], q["now"])
    return score(q, q["order"], q["now"], f, judge(text, f.lines))


def test_vague_abstention_fails():
    q = _dev("d11")
    assert _score_text(q, "Order 250 is at an unknown station.").stage == "GENERATION"
    assert _score_text(q, "There is no reason to say where it is.").stage == "GENERATION"
    assert _score_text(q, REFUSAL).stage == "NONE"
    assert _score_text(q, "Order 250 is not in the log.").stage == "NONE"


def test_conformance_needs_the_negative_verdict():
    q = _dev("d08")
    assert _score_text(q, "Yes, order 33 followed the recipe, although buffer_board is missing [e1002].").stage \
        == "GENERATION"
    assert _score_text(q, "No: order 33 skipped buffer_board [e1002].").stage == "NONE"


def test_contrasting_answers_are_not_rejected():
    assert _score_text(_dev("d03"), "Order 1 is parts_test, not gadget: mill_part decided it [e17].").stage == "NONE"
    assert _score_text(_dev("d07"), "engrave_gadget is running for 200 s; it is not stuck and not unusual [e54].") \
        .stage == "NONE"
    assert _score_text(_dev("d09"), "Yes, the fail branch is conformant: no deviation [e65].").stage == "NONE"
    assert _score_text(_dev("d09"), "No, it isn't conformant despite the fail branch [e65].").stage == "GENERATION"


def test_an_id_of_the_gold_line_counts_as_cited():
    """A line is one statement: citing e55 of the line [e54, e55, e56] cites the gold event e54."""
    f = _finding()
    row = score(_q(), "order:1", 1400, f, judge("engrave_gadget is open for 482 s, unusual [e55].", f.lines))
    assert (row.stage, row.cited_gold) == ("NONE", 1.0)


def test_every_generation_failure_says_why():
    f = _finding()
    refused = score(_q(), "order:1", 1400, f, judge(f"engrave_gadget is unusual [e54]. {REFUSAL}", f.lines))
    assert refused.stage == "GENERATION" and "refused, although the lines answer" in refused.notes
    uncited = score(_q(), "order:1", 1400, f, judge("engrave_gadget is unusual [e17].", f.lines))
    assert uncited.stage == "GENERATION" and "cites no line that holds a gold event" in uncited.notes


def test_a_copy_of_the_lines_is_not_an_answer():
    """The echo baseline has every fact and id, but it copies the lines: it does not answer."""
    from pmlab.answer import echo
    f = _finding()
    row = score(_q(), "order:1", 1400, f, judge(echo(f.lines), f.lines))
    assert row.stage == "GENERATION" and any(n.startswith("copies ") for n in row.notes)
    assert echo([]) == REFUSAL and echo(["order:9 is not in the log train (derived)"]) == REFUSAL
