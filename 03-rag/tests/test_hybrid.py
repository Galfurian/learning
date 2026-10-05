from raglab.corpus import Chunk
from raglab.hybrid import BM25, idf, rrf
from raglab.index import Hit


def chunk(cid, text):
    return Chunk(cid, cid.rsplit("-", 1)[0], "Demo", "T", text)


CHUNKS = [
    chunk("a-1", "PN-X7Q-991-A focus lens 38 mm"),
    chunk("b-1", "PN-X7Q-919-A first mirror gold"),
    chunk("c-1", "PN-X7R-919-A heater cartridge"),
]


def test_idf_weights():
    weights = idf(CHUNKS)
    assert weights["pn-x7q-919-a"] == weights["gold"]          # df = 1 for both
    assert weights["pn-x7q-919-a"] > idf(CHUNKS + [chunk("d-1", "PN-X7Q-919-A")])["pn-x7q-919-a"]  # more df, less weight
    assert "lens" in weights and "the" not in weights          # stopwords are not tokens


def test_bm25_finds_the_exact_identifier():
    hits = BM25(CHUNKS).search("What is PN-X7Q-919-A?", k=3)
    assert hits[0].chunk.id == "b-1" and hits[0].kind == "bm25"
    assert len(hits) == 1  # the other identifiers are different tokens


def test_bm25_no_match_returns_nothing():
    assert BM25(CHUNKS).search("warranty period", k=3) == []


def test_rrf():
    def ranked(*ids):
        return [Hit(chunk(i, ""), 1.0, r) for r, i in enumerate(ids, start=1)]

    fused = rrf([ranked("a-1", "b-1"), ranked("b-1", "c-1")])
    assert [h.chunk.id for h in fused] == ["b-1", "a-1", "c-1"]
    assert fused[0].kind == "rrf" and abs(fused[0].score - (1 / 62 + 1 / 61)) < 1e-12
    assert [h.rank for h in fused] == [1, 2, 3]
    assert len(rrf([ranked("a-1", "b-1")], limit=1)) == 1
