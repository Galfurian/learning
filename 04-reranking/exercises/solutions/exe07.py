"""EXE07 — which stage failed first? Task: see README.md in this folder."""

from reranklab.runners import run_diagnosis


def diagnose(row: dict) -> str:
    if not row["answerable"]:
        return "NONE" if row["refused"] else "GENERATION"
    if not any(c["gain"] == 2 for c in row["candidates"]):
        return "CANDIDATES"
    if not any(c["gain"] == 2 for c in row["top"]):
        return "RERANK"
    if not (row["facts"] and row["citations_ok"]):
        return "GENERATION"
    return "NONE"


if __name__ == "__main__":
    run_diagnosis(diagnose, __file__)
