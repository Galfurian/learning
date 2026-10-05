from raglab.ui import shorten_vectors


def test_shorten_vectors_keeps_small_lists_and_cuts_long_float_lists():
    body = {"input": ["a", "b"], "embeddings": [[0.1] * 768, [0.2] * 768], "dims": [1, 2]}
    short = shorten_vectors(body)
    assert short["input"] == ["a", "b"] and short["dims"] == [1, 2]
    assert short["embeddings"][0] == [0.1, 0.1, 0.1, 0.1, "\u2026 764 more floats (768 total)"]
