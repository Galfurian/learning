# EXE04 — A score on an ordered scale

**Concept:** a `score` question has ordered levels. The model returns a
probability per level and a `score`: the **expected level**,
`sum(index * probability)`. It is a number, so your code can compare it with
thresholds. But an average can hide a disagreement.

## Task

1. In `QUESTIONS`, add one question named `satisfaction`, of type `score`,
   with `criteria` set to `LEVELS` (from `"Very unhappy"` at index 0 to
   `"Very happy"` at index 4).
2. Implement `act(review, answers)` with this table:

   | `score`          | Action                                        |
   |------------------|-----------------------------------------------|
   | below 1.5        | `"open a support case and call the customer"` |
   | 1.5 to below 3.5 | `"send a thank-you email"`                    |
   | 3.5 or more      | `"invite the customer to the referral program"` |

The answer you receive has this shape:

```python
answers = {"satisfaction": {
    "type": "score", "score": 1.97,
    "legend": {"0": "Very unhappy", "1": "Unhappy", "2": "Neutral", "3": "Happy", "4": "Very happy"},
    "probabilities": {"0": 0.0, "1": 0.06, "2": 0.91, "3": 0.03, "4": 0.0},
    "confidence": 0.75}}
```

## Verify

```bash
uv run python exercises/exe04-score/check.py
uv run python exercises/exe04-score/exe04.py
```

## Think about it

- The last test in `check.py` gives half the probability to "Very unhappy" and
  half to "Very happy". The score is 2.0, "Neutral", and your code sends a
  thank-you email. Nobody thought the review was neutral. What in the answer
  tells you that? (Look at `confidence`.)
- Write `LEVELS` in the wrong order (`"Very happy"` first) and run again. The
  model is not confused, but your thresholds are now wrong. Why?
- Compare with a `choice` question with the same five options. When is the
  order important enough to use `score`?
- Review 4 ("Good quality but the delivery was late") mixes a good and a bad
  point. Look at its probabilities. Is it one opinion or two?
