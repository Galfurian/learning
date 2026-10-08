"""EXE07 — which stage failed first? Task: see README.md in this folder."""

from reranklab.runners import run_diagnosis


# TODO: return the FIRST failing stage of one recorded row, in this fixed order.
# A row has: answerable (bool), refused (bool), facts (bool), citations_ok (bool),
#   candidates: the first stage's N hits, top: the k hits after reranking;
#   every hit has a "gain" (2 = evidence chunk).
# answerable question:
#   no gain-2 hit among the candidates                 -> "CANDIDATES"
#   a gain-2 hit among the candidates, none in top     -> "RERANK"
#   a gain-2 hit in top, but facts or citations fail   -> "GENERATION"
#   otherwise                                          -> "NONE"
# no-answer question: refused -> "NONE", otherwise -> "GENERATION"
def diagnose(row: dict) -> str:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_diagnosis(diagnose, __file__)
