# EXE01 — Your first question

**Concept:** a question is data you send, not code you register. A `noul`
question asks "is this true?", and the answer is a probability. Turning that
probability into yes or no is a decision of **your** code.

## Before you start

Run the exercise as it is:

```bash
uv run python exercises/exe01-first-question/exe01.py
```

`QUESTIONS` is empty, and Ollama rejects the request:
`questions must contain 1–64 fields`. A decision model only answers the
questions you ask.

## Task

Anna wants emails that ask for a meeting to go to her calendar.

1. In `QUESTIONS`, add one question named `meeting`, of type `noul`, with
   `instructions` that ask whether the sender wants to schedule a meeting.
   Write it as a yes/no question.
2. Implement `act(email, answers)`: return `"calendar"` when the probability
   is at least `THRESHOLD`, otherwise `"inbox"`.

The answer you receive has this shape:

```python
answers = {"meeting": {"type": "noul", "noul": 0.98}}
```

## Verify

```bash
uv run python exercises/exe01-first-question/check.py
uv run python exercises/exe01-first-question/exe01.py --inspect
uv run python exercises/exe01-first-question/exe01.py
uv run python exercises/exe01-first-question/exe01.py --verbose
```

## Hints

- Look at the `refund` question in `exercises/exe00-demo/exe00.py`.
- The name of the question is the key of the answer.

## Think about it

- Email 3 ("Thanks for yesterday's call") mentions a call. What is its
  probability? Change the wording of `instructions` (for example "Does the
  email mention a meeting?") and run again. The instructions are the question:
  a different question gets a different answer.
- Email 4 never says "meeting". Why can the model still answer high?
- Who decided that 0.5 is the line? What would you change if a missed meeting
  cost much more than a wrong calendar entry?
- Run the same command twice. Are the numbers identical? (A decision model
  does not sample.) And the times? See "Why the second run is much faster" in
  [docs/mental-model.md](../../docs/mental-model.md).
