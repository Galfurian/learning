import numpy as np

from raglab.checks import fake_chunk, fake_hits, run_checks
from raglab.evalset import Question


def question(qid, relevant):
    return Question(qid, "x", frozenset(relevant), "c", "", ())


def checks(exe, check):
    chunks = [fake_chunk("a-1"), fake_chunk("b-1"), fake_chunk("c-1")]
    vectors = np.array([[1.0, 0.0], [0.0, 1.0], [0.6, 0.8]])
    done, hits = check.calls(exe.search, vectors, chunks, np.array([0.0, 1.0]), 2)
    if not done:
        return
    check.ok([h.chunk.id for h in hits] == ["b-1", "c-1"], "best first", [h.chunk.id for h in hits])
    check.ok([h.rank for h in hits] == [1, 2], "ranks start at 1")
    check.ok(abs(hits[1].score - 0.8) < 1e-6 and isinstance(hits[1].score, float), "score is the dot product, as a float")
    check.ok(len(exe.search(vectors, chunks, np.array([1.0, 0.0]), 10)) == 3, "k larger than the corpus returns all")
    questions = [question("q1", {"a"}), question("q2", {"b"}), question("q3", set())]
    results = {"q1": fake_hits("a-1", "b-1"), "q2": fake_hits("c-1", "b-1"), "q3": fake_hits("a-1")}
    done, r1 = check.calls(exe.recall_at_k, questions, results, 1)
    if not done:
        return
    check.ok(r1 == 0.5, "R@1 = 0.5: one of the two answerable questions", r1)
    check.ok(exe.recall_at_k(questions, results, 2) == 1.0, "R@2 = 1.0; the no-answer question is not counted")
    try:
        exe.recall_at_k([question("q3", set())], results, 3)
        check.ok(False, "no answerable question raises ValueError")
    except ValueError:
        check.ok(True, "no answerable question raises ValueError")


run_checks(checks, __file__.replace("check.py", "exe04.py"))
