"""EXE07 — diagnose the first failing stage. Task: see README.md in this folder."""

from kglab.runners import run_diagnosis


# TODO: return the first failing stage in this order:
# - an unanswerable question with nodes is PLAN; without nodes it is NONE when
#   answer_ok is true, otherwise GENERATION;
# - missing_edges are RESOLUTION when a missing edge's (source, relation) is in
#   dropped_relations, otherwise EXTRACTION;
# - then check path_ok, the start-node sets, answer_ok, and finally NONE.
def diagnose(row: dict) -> str:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_diagnosis(diagnose, __file__)
