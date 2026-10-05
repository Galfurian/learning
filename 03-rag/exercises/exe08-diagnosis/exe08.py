"""EXE08 — which stage failed? Task: see README.md in this folder."""

from raglab.generation import REFUSAL
from raglab.runners import run_diagnosis

STAGES = ("RETRIEVAL", "CONTEXT", "GENERATION", "NONE")


# TODO: return the FIRST point of failure of one recorded trace, applying
# the rules in README.md in order. A trace is a dict with:
#   relevant   section ids that answer the question ([] = no answer exists)
#   hits       [{"id", "section_id", "score", "rank"}, ...] what retrieval returned
#   context    [{"id", "section_id"}, ...] what the generator read
#   answer, abstained
#   labels     {"answer_correct": bool | None, "supported": bool | None}, written by a person
# Do not judge the answer text yourself: use the labels, and REFUSAL for
# no-answer questions.
def diagnose(trace: dict) -> str:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_diagnosis(diagnose, __file__)
