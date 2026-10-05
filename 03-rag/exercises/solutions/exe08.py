"""EXE08 — which stage failed? Task: see README.md in this folder."""

from raglab.generation import REFUSAL
from raglab.runners import run_diagnosis

STAGES = ("RETRIEVAL", "CONTEXT", "GENERATION", "NONE")


def diagnose(trace: dict) -> str:
    relevant = set(trace["relevant"])
    if not relevant:
        refused = trace["abstained"] or REFUSAL.lower().rstrip(".") in trace["answer"].lower()
        return "NONE" if refused else "GENERATION"
    if not any(h["section_id"] in relevant for h in trace["hits"]):
        return "RETRIEVAL"
    if not any(c["section_id"] in relevant for c in trace["context"]):
        return "CONTEXT"
    labels = trace["labels"]
    if labels["answer_correct"] is False or labels["supported"] is False:
        return "GENERATION"
    return "NONE"


if __name__ == "__main__":
    run_diagnosis(diagnose, __file__)
