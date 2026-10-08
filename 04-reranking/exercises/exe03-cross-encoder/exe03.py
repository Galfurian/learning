"""EXE03 — the cross-encoder. Task: see README.md in this folder."""

import numpy as np

from reranklab.runners import run_cross_encoder


# TODO: score one (question, passage) pair with the cross-encoder.
# 1. encoding = tokenizer.encode(question, passage): ONE token sequence for the pair,
#    [CLS] question [SEP] passage [SEP]; encoding.ids, encoding.attention_mask, encoding.type_ids.
# 2. Build the inputs, each a numpy int64 array of shape (1, n):
#    "input_ids", "attention_mask", and "token_type_ids" only if the model has that input
#    (names = {i.name for i in session.get_inputs()}).
# 3. outputs = session.run(None, inputs); the relevance score is outputs[0] reshaped to one value.
# Return it as a Python float. Do not apply a sigmoid.
def score_pair(tokenizer, session, question: str, passage: str) -> float:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_cross_encoder(score_pair, __file__)
