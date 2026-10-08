import numpy as np

from reranklab.checks import run_checks


class Encoding:
    ids, attention_mask, type_ids = [101, 7, 102, 9, 102], [1, 1, 1, 1, 1], [0, 0, 0, 1, 1]


class Tokenizer:
    def __init__(self):
        self.pairs = []

    def encode(self, a, b):
        self.pairs.append((a, b))
        return Encoding()


class Input:
    def __init__(self, name):
        self.name = name


class Session:
    def __init__(self, names, logit=-3.25):
        self.names, self.logit, self.feed = names, logit, None

    def get_inputs(self):
        return [Input(n) for n in self.names]

    def run(self, outputs, feed):
        self.feed = feed
        return [np.array([[self.logit]], dtype=np.float32)]


def checks(exe, check):
    tokenizer, session = Tokenizer(), Session(["input_ids", "attention_mask", "token_type_ids"])
    done, value = check.calls(exe.score_pair, tokenizer, session, "question?", "passage.")
    if not done:
        return
    check.ok(tokenizer.pairs == [("question?", "passage.")], "the tokenizer encodes the pair together, question first")
    check.ok(isinstance(value, float) and abs(value + 3.25) < 1e-6, "returns the raw logit as a float (no sigmoid)", value)
    feed = session.feed or {}
    check.ok(set(feed) == {"input_ids", "attention_mask", "token_type_ids"}, "feeds the three inputs the model has", set(feed))
    check.ok(all(v.dtype == np.int64 and v.shape == (1, 5) for v in feed.values()), "int64 arrays of shape (1, n)")
    check.ok(feed["token_type_ids"].tolist() == [[0, 0, 0, 1, 1]], "token_type_ids mark question (0) and passage (1)")
    two = Session(["input_ids", "attention_mask"], logit=1.0)
    exe.score_pair(Tokenizer(), two, "q", "p")
    check.ok(set(two.feed) == {"input_ids", "attention_mask"}, "no token_type_ids when the model has no such input")


run_checks(checks, __file__.replace("check.py", "exe03.py"))
