"""EXE03 — the cross-encoder. Task: see README.md in this folder."""

import numpy as np

from reranklab.runners import run_cross_encoder


def score_pair(tokenizer, session, question: str, passage: str) -> float:
    encoding = tokenizer.encode(question, passage)
    inputs = {
        "input_ids": np.array([encoding.ids], dtype=np.int64),
        "attention_mask": np.array([encoding.attention_mask], dtype=np.int64),
    }
    if "token_type_ids" in {i.name for i in session.get_inputs()}:
        inputs["token_type_ids"] = np.array([encoding.type_ids], dtype=np.int64)
    return float(np.asarray(session.run(None, inputs)[0]).reshape(-1)[0])


if __name__ == "__main__":
    run_cross_encoder(score_pair, __file__)
