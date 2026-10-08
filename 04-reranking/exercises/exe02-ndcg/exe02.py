"""EXE02 — graded relevance and nDCG. Task: see README.md in this folder."""

import math

from reranklab.corpus import Chunk
from reranklab.evalset import Question
from reranklab.runners import run_ndcg


# TODO: the gain of a chunk for a question:
#   2  the chunk is from a relevant section (chunk.section_id in question.relevant)
#      and contains every string of question.must_contain (case-insensitive)  -> an evidence chunk
#   1  the chunk is from a relevant section, without all the facts
#   0  otherwise
def gain(chunk: Chunk, question: Question) -> int:
    raise NotImplementedError("You need to implement this function.")


# TODO: nDCG@k = DCG@k(gains) / DCG@k(ideal), with
#   DCG@k(g) = sum over the first k positions i = 1, 2, ... of (2**g_i - 1) / log2(i + 1).
# `gains` are the gains of the ranked hits; `ideal` is the best possible list.
# When DCG@k(ideal) is 0, return 0.0.
def ndcg_at_k(gains: list[int], ideal: list[int], k: int) -> float:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_ndcg(gain, ndcg_at_k, __file__)
