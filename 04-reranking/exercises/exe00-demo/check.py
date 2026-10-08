from reranklab.checks import fake_chunk, run_checks
from reranklab.index import Hit
from reranklab.rerankers import FakeReranker, rerank


def checks(exe, check):
    hits = [Hit(fake_chunk("a-1", "door seal"), 0.9, 1, first_rank=1),
            Hit(fake_chunk("b-1", "belt speed 32 m/min"), 0.5, 2, first_rank=2)]
    top = rerank("belt speed", hits, FakeReranker(), k=1)
    check.ok([h.chunk.id for h in top] == ["b-1"], "the reranker moves the relevant candidate to rank 1")
    check.ok(top[0].first_rank == 2, "the hit remembers its first-stage rank")
    check.ok(len(rerank("belt speed", hits, FakeReranker(), k=5)) == 2, "nothing is added: 2 candidates in, 2 out")
    check.ok(callable(exe.run_demo), "exe00 runs the shared demo")


run_checks(checks, __file__.replace("check.py", "exe00.py"))
