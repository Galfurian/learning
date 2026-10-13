"""EXE07 — diagnose the first failing stage. Task: see README.md in this folder."""

from kglab.runners import run_diagnosis


def diagnose(row: dict) -> str:
    if not row["answerable"]:
        if row["nodes"]:
            return "PLAN"
        return "NONE" if row["answer_ok"] else "GENERATION"

    dropped = {(item[0], item[1]) for item in row["dropped_relations"]}
    if row["missing_edges"]:
        if any((edge[3], edge[1]) in dropped for edge in row["missing_edges"]):
            return "RESOLUTION"
        return "EXTRACTION"
    if not row["path_ok"]:
        return "PLAN"
    if set(row["starts"]) != set(row["gold_starts"]):
        return "LINKING"
    if not row["answer_ok"]:
        return "GENERATION"
    return "NONE"


if __name__ == "__main__":
    run_diagnosis(diagnose, __file__)
