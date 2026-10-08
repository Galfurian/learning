"""EXE04 — the decision model as a reranker. Task: see README.md in this folder."""

from reranklab.runners import run_tev1


def state_a(question: str, passage: str) -> str:
    return f"Question: {question}\n\nPassage:\n{passage}"


QUESTION_A = {"relevant": {"type": "noul", "instructions": "Does the passage contain the answer to the question?"}}


def state_b(question: str, passages: list[str]) -> str:
    body = "\n\n".join(f"Passage {i}:\n{p}" for i, p in enumerate(passages, start=1))
    return f"Question: {question}\n\n{body}"


def questions_b(n: int) -> dict:
    return {f"p{i}": {"type": "noul", "instructions": f"Does passage {i} contain the answer to the question?"}
            for i in range(1, n + 1)}


if __name__ == "__main__":
    run_tev1(__import__(__name__), __file__)
