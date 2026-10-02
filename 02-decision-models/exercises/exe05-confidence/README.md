# EXE05 — Probabilities and confidence

**Concept:** the probabilities are the most useful part of the answer. From
them your code can tell a clear case from a close call, and decide when it may
act alone and when a person must look. Ollama's `confidence` is one summary of
them; you recompute it, and you learn what it does **not** say.

## Task

`exe05.py` moderates forum posts. The question is written. Implement three
functions:

1. `confidence(probabilities)`: `1 - H / ln(N)`, where
   `H = -sum(p * ln p)` is the entropy of the distribution and `N` the number
   of options. Skip zero probabilities in the sum (`0 * ln 0` counts as 0).
   Do not read `answer["confidence"]`: the check compares your number with
   the values Ollama returned.
2. `margin(probabilities)`: the best probability minus the second best.
3. `act(post, answers)`: act alone only when the probability of the chosen
   option reaches its threshold in `THRESHOLDS`:
   - above the threshold: return the `ACTIONS` entry, for example
     `"delete (p=0.97, confidence 0.85, margin 0.95)"`;
   - below it: return a string that starts with
     `"send to a human moderator"`, followed by the evidence.

The evidence in parentheses is for the person who reads the log. The check
only looks at the first words.

## Verify

```bash
uv run python exercises/exe05-confidence/check.py
uv run python exercises/exe05-confidence/exe05.py
```

## Think about it

- Case 3 ("You are an idiot...") is a clear insult. What is `p["insult"]`, and
  what is the confidence? With three options, a probability of 0.8 already
  gives a confidence below 0.5. Which number is easier to choose a threshold
  for?
- Case 4 ("This tutorial is garbage, whoever wrote it should be fired") is
  harsh criticism of a tutorial, plus a wish about a person. Is it an insult?
  Compare the model's numbers for case 3 and case 4. Does the probability tell
  you that case 4 is the harder one? Confidence measures how concentrated the
  distribution is, not whether the model is right.
- Why does `spam` need 0.9 and `normal` only 0.8? Who pays for each kind of
  mistake?
- A `noul` answer has no `confidence` field. Write the same formula for one
  probability `p` (two options: `p` and `1 - p`). What is the confidence of
  `p = 0.5`? Of `p = 0.98`?
- How would you check, with real data, that a probability of 0.9 is right 9
  times out of 10?
