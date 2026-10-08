"""EXE04 — the decision model as a reranker. Task: see README.md in this folder."""

from reranklab.runners import run_tev1


# TODO (mode A, one request per passage): the state holds the question and ONE passage:
#   "Question: <question>\n\nPassage:\n<passage>"
def state_a(question: str, passage: str) -> str:
    raise NotImplementedError("You need to implement this function.")


# TODO (mode A): one noul question named "relevant", whose instructions ask whether
# the passage contains the answer to the question.
QUESTION_A: dict = {}


# TODO (mode B, one request for all passages): the state holds the question and EVERY
# passage, numbered from 1:
#   "Question: <question>\n\nPassage 1:\n<p1>\n\nPassage 2:\n<p2> ..."
def state_b(question: str, passages: list[str]) -> str:
    raise NotImplementedError("You need to implement this function.")


# TODO (mode B): one noul question per passage, named "p1" ... "pN"; the instructions of
# "pI" ask whether passage I contains the answer to the question.
def questions_b(n: int) -> dict:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_tev1(__import__(__name__), __file__)
