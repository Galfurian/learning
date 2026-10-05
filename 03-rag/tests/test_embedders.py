import numpy as np
from raglab import embedders
from raglab.cache import EmbeddingCache
from raglab.embedders import FakeEmbedder, OllamaEmbedder, tokens


def test_tokens_keep_identifiers_and_drop_stopwords():
    assert tokens("What does E-4021 mean for PN-X7Q-991-A at 0.8 m/s?") == [
        "e-4021", "mean", "pn-x7q-991-a", "0.8", "m/s",
    ]


def test_fake_embedder_is_deterministic_and_unit_length():
    fake = FakeEmbedder(dim=64)
    a = fake.embed_query("belt tension squeal")
    assert np.allclose(a, fake.embed_query("belt tension squeal"))
    assert abs(np.linalg.norm(a) - 1.0) < 1e-6


def test_fake_embedder_raw_counts():
    raw = FakeEmbedder(dim=64, normalized=False).embed_query("belt belt belt")
    assert raw.max() == 3.0


def test_fake_embedder_zero_vector_for_stopwords_only():
    vector = FakeEmbedder(dim=64).embed_query("what is it?")
    assert not np.isnan(vector).any()
    assert np.linalg.norm(vector) == 0.0


def test_fake_documents_shape():
    out = FakeEmbedder(dim=32).embed_documents(["a cat", "a dog"], ["t1", "t2"])
    assert out.shape == (2, 32) and out.dtype == np.float32
    assert FakeEmbedder(dim=32).embed_documents([]).shape == (0, 32)


def test_prefix_formats():
    gemma = OllamaEmbedder("embeddinggemma")
    assert gemma.format_query("q") == "task: search result | query: q"
    assert gemma.format_document("d", "Cooling") == "title: Cooling | text: d"
    assert gemma.format_document("d", None) == "title: none | text: d"
    assert OllamaEmbedder("embeddinggemma:latest").format_query("q").startswith("task:")
    raw = OllamaEmbedder("embeddinggemma", prefixed=False)
    assert raw.format_query("q") == "q" and raw.format_document("d", "T") == "d"
    assert OllamaEmbedder("all-minilm").format_query("q") == "q"


def test_cache_key_depends_on_model_and_text(tmp_path):
    cache = EmbeddingCache(tmp_path)
    assert cache.key("m", "x") != cache.key("m", "y")
    assert cache.key("m", "x") != cache.key("n", "x")
    assert cache.get("m", "x") is None
    cache.put("m", "x", np.array([1.0, 0.0], dtype=np.float32))
    assert np.allclose(cache.get("m", "x"), [1.0, 0.0])
    assert cache.get("n", "x") is None


def test_ollama_embedder_uses_cache_and_batches(monkeypatch, tmp_path):
    sent = []

    def fake_embed(model, texts, tracer=None):
        sent.append(list(texts))
        return type("R", (), {"vectors": [[1.0, 0.0] for _ in texts]})()

    monkeypatch.setattr(embedders, "embed", fake_embed)
    embedder = OllamaEmbedder("embeddinggemma", cache=EmbeddingCache(tmp_path), batch=2)
    out = embedder.embed_documents(["a", "b", "c"], ["t", "t", "t"])
    assert out.shape == (3, 2)
    assert [len(batch) for batch in sent] == [2, 1]
    assert sent[0][0] == "title: t | text: a"
    embedder.embed_documents(["a", "b", "c"], ["t", "t", "t"])
    assert len(sent) == 2 and embedder.cached == 3
    # Another prefix setting is another text: no reuse.
    OllamaEmbedder("embeddinggemma", prefixed=False, cache=EmbeddingCache(tmp_path)).embed_documents(["a"])
    assert sent[-1] == ["a"]


def test_queries_are_not_cached_so_verbose_always_shows_the_call(monkeypatch, tmp_path):
    sent = []

    def fake_embed(model, texts, tracer=None):
        sent.append(list(texts))
        return type("R", (), {"vectors": [[1.0, 0.0] for _ in texts]})()

    monkeypatch.setattr(embedders, "embed", fake_embed)
    embedder = OllamaEmbedder("embeddinggemma", cache=EmbeddingCache(tmp_path))
    embedder.embed_query("q")
    embedder.embed_query("q")
    assert len(sent) == 2
