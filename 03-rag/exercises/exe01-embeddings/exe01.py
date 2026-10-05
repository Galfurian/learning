"""EXE01 — texts become vectors. Task: see README.md in this folder."""

import numpy as np

from raglab.runners import run_embeddings

# Sentence pairs: (a, b, "same" or "different" meaning).
PAIRS = [
    ("The belt squeals at start-up.", "The conveyor belt makes a high-pitched noise when it starts.", "same"),
    ("Keep the coolant between 15 and 22 °C.", "The chiller water must stay cool.", "same"),
    ("My prints don't stay attached to the plate.", "The first layer does not stick to the build sheet.", "same"),
    ("Never cut PVC on the laser.", "PVC must not be cut on the laser.", "same"),
    ("The nozzle is clogged.", "The nozzle is clean.", "different"),
    ("Lower the conveyor speed.", "Lower the oven temperature.", "different"),
    ("E-4021: the lid interlock opened.", "E-4012: the air pressure is too low.", "different"),
    ("Clean the lens every week.", "Grease the rails every 1000 hours.", "different"),
    # TODO: add two pairs of your own: one where you expect the FakeEmbedder
    # to fail, and one where you expect the real model to fail.
]


# TODO: return the vector divided by its length (L2 norm).
# A zero vector has no direction: return it unchanged, without dividing by 0.
# Do not modify the input array.
def normalize(vector: np.ndarray) -> np.ndarray:
    raise NotImplementedError("You need to implement this function.")


if __name__ == "__main__":
    run_embeddings(PAIRS, normalize, __file__)
