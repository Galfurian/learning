from raglab.checks import fake_chunk, run_checks
from raglab.index import Hit


def checks(exe, check):
    chunks = [
        fake_chunk("a-1", "PN-X7Q-991-A focus lens"),
        fake_chunk("b-1", "PN-X7Q-919-A first mirror"),
        fake_chunk("c-1", "first mirror cleaning"),
    ]
    weights = {"pn-x7q-991-a": 2.0, "pn-x7q-919-a": 2.0, "first": 0.5, "mirror": 0.5, "focus": 1.0,
               "lens": 1.0, "cleaning": 1.0}
    done, hits = check.calls(exe.keyword_search, chunks, weights, "What is PN-X7Q-919-A, the first mirror?", 3)
    if not done:
        return
    check.ok([h.chunk.id for h in hits] == ["b-1", "c-1"], "exact identifier first; no score-0 chunks", [h.chunk.id for h in hits])
    check.ok(abs(hits[0].score - 3.0) < 1e-9, "score = sum of weights of distinct shared tokens (2 + 0.5 + 0.5)", hits[0].score)
    check.ok([h.rank for h in hits] == [1, 2] and hits[0].kind == "keyword", "ranks from 1, kind 'keyword'")
    check.ok(exe.keyword_search(chunks, weights, "mirror mirror mirror", 3)[0].score == 0.5, "a repeated query word counts once")
    check.ok(exe.keyword_search(chunks, weights, "warranty", 3) == [], "no shared token: no hits")

    def ranked(*ids):
        return [Hit(fake_chunk(i), 1.0, r) for r, i in enumerate(ids, start=1)]

    done, fused = check.calls(exe.fuse, [ranked("a-1", "b-1"), ranked("b-1", "c-1")])
    if not done:
        return
    check.ok([h.chunk.id for h in fused] == ["b-1", "a-1", "c-1"], "a chunk in both rankings wins", [h.chunk.id for h in fused])
    check.ok(abs(fused[0].score - (1 / 62 + 1 / 61)) < 1e-12, "score = sum of 1 / (60 + rank)")
    check.ok([h.rank for h in fused] == [1, 2, 3] and fused[0].kind == "rrf", "new ranks from 1, kind 'rrf'")


run_checks(checks, __file__.replace("check.py", "exe07.py"))
