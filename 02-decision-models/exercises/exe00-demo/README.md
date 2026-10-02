# EXE00 — A solved example

**Concept:** the whole loop, end to end, on a file that already works. There
is nothing to write here. Sections 3 and 4 of the
[unit README](../../README.md) walk through it step by step.

`exe00.py` triages three support tickets. It asks two questions about each
ticket: which team should handle it (`choice`) and whether the customer asks
for money back (`noul`). Then `act()` puts the ticket in a queue.

## Try every command

```bash
uv run python exercises/exe00-demo/check.py              # the app code, with fake answers, no model
uv run python exercises/exe00-demo/exe00.py --inspect    # the requests the app would send
uv run python exercises/exe00-demo/exe00.py              # the model decides, the app acts
uv run python exercises/exe00-demo/exe00.py --verbose    # every HTTP request and response
uv run python exercises/exe00-demo/exe00.py --case 2     # only the second ticket
uv run python exercises/exe00-demo/exe00.py --state "I was billed 49 euros but my plan costs 39. Why?"
```

## Think about it

- In the `--verbose` trace, find the line where the model's work ends. Which
  function turns `0.98` into "tagged 'refund-request'"?
- Run the `--state` example above. Is it a refund request? What does the
  `refund` probability say, and what does the app do with it?
- `check.py` never calls the model, yet it verifies the app's behavior. How?
- Every other exercise file has the same shape as this one: `CASES`,
  `QUESTIONS`, `act()` (and sometimes `build_state()`), then
  `run(QUESTIONS, CASES, __file__, ...)`.
