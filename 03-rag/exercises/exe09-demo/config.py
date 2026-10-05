"""Settings of the final system, chosen on the DEV set in EXE03–EXE07.

The holdout set (data/plant/holdout.json) is not used to choose any of them.
"""

SIZE = 60             # EXE03: 60 and 120 tie on the dev set with embeddinggemma (E@1 0.955); 15 is worse
OVERLAP = 15
K = 3                 # EXE04: R@3 = E@3 = 1.000 on the dev set; R@1 = 0.955
BUDGET = 1500         # EXE05: three chunks of the dev set use about 150–250 estimated tokens
MIN_SCORE = None      # EXE05: the cheapest threshold (0.33) refused 1 of 4 no-answer questions, and the
                      # generator refused all 4 anyway (EXE06): no threshold, the refusal is the check
RETRIEVER = "semantic"  # EXE07: semantic R@3 1.000 vs fused 0.955 on the dev set
NUM_CTX = 8192        # generator context window, tokens
STUFF_BUDGET = 7000   # --mode stuff: estimated tokens of manuals that fit in NUM_CTX with the question
