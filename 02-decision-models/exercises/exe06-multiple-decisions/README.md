# EXE06 — Several decisions about one state

**Concept:** one request can carry up to 64 named questions about the same
state. Each one comes back as a separate answer, and **your code** combines
them into one action. Asking them together is cheaper in time, but they are
not guaranteed to be independent: on a small model, the presence of one
question can move the answer to another.

## Task

`exe06.py` triages bug reports. `COMPONENTS` and `SEVERITY` are given.

1. Write three questions in `QUESTIONS`:
   - `component`: `choice` over `COMPONENTS`, "Which part of the system is
     the bug report about?";
   - `severity`: `score` over `SEVERITY`, "How severe is the problem described
     in the bug report?";
   - `reproducible`: `noul`, "Does the report say what the user did, or which
     error they got?".
2. Implement `act(report, answers)` with these rules, in this order:
   1. severity score of 2.5 or more: `"page the on-call engineer (<component>)"`;
   2. not reproducible (probability below 0.5), or component `unknown`:
      `"ask the reporter for steps and the error message"`;
   3. otherwise: `"add to the <component> backlog"`.

The model never sees these rules. It answers three narrow questions; the rules
are your application.

## Verify

```bash
uv run python exercises/exe06-multiple-decisions/check.py
uv run python exercises/exe06-multiple-decisions/exe06.py
```

## Together or separately

By default the runner sends the three questions in one request. Run the same
cases with one request per question:

```bash
uv run python exercises/exe06-multiple-decisions/exe06.py --separately
```

Compare the two summaries. Compare times only on the first run of each
command: Ollama caches repeated requests, so a second run of the same command
is much faster and tells you nothing about cost (see "Why the second run is
much faster" in [docs/mental-model.md](../../docs/mental-model.md)).

- the total time and the `input_tokens`;
- the `reproducible` probability of each case. On one run of
  `tev1:4b-q4_K_M` it went from 0.95 to 0.65 for case 2, and from 0.07 to
  0.34 for case 1, just by changing how the questions were sent.

Then repeat both runs with the small model. Before you switch, unload the big
one, so only one model is in memory:

```bash
ollama stop tev1:4b-q4_K_M
uv run python exercises/exe06-multiple-decisions/exe06.py --model tev1:0.8b
uv run python exercises/exe06-multiple-decisions/exe06.py --model tev1:0.8b --separately
```

## Think about it

- If one decision must be stable (for example, it triggers a page at night),
  would you ask it together with others or alone?
- Rule 1 pages before looking at `reproducible`. Why is the order of the
  rules part of the design, and why is it in code?
- `severity` is only useful when `component` is not `unknown`. Write a two-step
  version: ask `component` first, and ask `severity` only when needed. What
  does it cost, and what does it save?
- Which of these three questions could be answered without a model, by
  ordinary code?
