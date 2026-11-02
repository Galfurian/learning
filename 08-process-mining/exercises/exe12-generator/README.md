# EXE12 — Improve the generator

EXE11 shows that SELECTION and MINING never fail: the evidence lines always
hold the gold events. Every failure is at GENERATION. In this exercise you
try to make the answers better, and you measure if you did.

You edit `SYSTEM_PROMPT` in `exe12.py`. It starts as a copy of the unit's
prompt (`pmlab.answer.SYSTEM_PROMPT`).

```bash
uv run python exercises/exe12-generator/exe12.py --baseline        # your prompt and the unit's, dev, 3 runs each
uv run python exercises/exe12-generator/exe12.py --model qwen3:4b-instruct-2507-q4_K_M
uv run python exercises/exe12-generator/exe12.py --holdout         # once, at the very end
```

The runner shows the right answers per question (of 3 runs) and the most
frequent failure notes.

## The rules

1. **Change one thing per experiment.** If you change six sentences and the
   score goes down, you do not know which sentence did it.
2. **Run 3 times.** The generator samples. The same prompt gave 4, 7 and 4
   of 12 on dev. A difference of one or two answers is noise.
3. **Compare with `--baseline`**, on the same day and the same model.
4. **Read the failing answers**, not only the count. The failure note says
   which check failed. Is it the model, or is it the rubric? If the rubric
   is wrong, fix the rubric on dev, and write down that you did.
5. **The holdout runs once**, with the prompt you chose on dev. If you tune
   on the holdout, it becomes a second dev set and tells you nothing.
6. **Write down the negative results.** A change that makes the score worse
   is a result.

## Before you start: what is the score worth?

Two checks were done when this unit was measured. Do them again in your
head before you trust a number.

- **The baseline of no model.** `exe11.py --echo` answers with the evidence
  lines themselves. Before the copy check, this answer scored 11 of 12 on
  dev: the rubric checked that the facts were in the text, not that the text
  answered the question. Now a verbatim copy of an evidence line of 40
  characters or more fails ("copies N evidence line(s) instead of
  answering"). The echo baseline now scores 1 of 12 on dev and 0 of 8 on
  holdout. A generator must beat it.
- **The audit of the failures.** Each GENERATION failure of the first runs
  was read by hand. See the unit README, section 5.

## Task

Find a change that makes dev better in 3 runs of 3, and explain why it
works with the failing answers. Then run the holdout once.

Some ideas, from the audit:

- The model echoes "The recipe stopped, I don't know why." and then refuses.
  The question is a statement of a problem, not a question.
- The model appends "Not in the recording." to a right answer.
- The model writes ids that are not in the lines.
- A larger model. Check what the model does with `think: false` first: see
  "Measured runs". Pull it first (`ollama pull qwen3:4b-instruct-2507-q4_K_M`,
  2.5 GB).

There is no solution file. We did not find a prompt that is better than the
unit's: see below. If you find one, the measured runs show how to prove it.

## Measured runs

Measured on 2026-11-02 on the local CPU (Intel Core Ultra 9 185H, WSL),
dev only, 3 runs each, `max_tokens` 400. Three runs of dev take about
3 minutes with `qwen3:1.7b` and about 8 minutes with the 4B instruct model.

| # | change from the control | model | right per run (of 12) | most frequent new failure |
|---|-------------------------|-------|-----------------------|---------------------------|
| e0 | none (control) | `qwen3:1.7b` | 5, 6, 6 | (refusals, missing terms) |
| e1 | six rules at once: a problem statement is a question, direct answer first, "does not show why" at the end, Yes or No first, a fail branch is not a deviation, refuse only with no line about the order | `qwen3:1.7b` | 2, 2, 2 | copies the lines (13); adds "does not show why" to every answer |
| e5 | one rule: a problem statement is a question | `qwen3:1.7b` | 2, 4, 4 | cites no line that holds a gold event (17) |
| e6 | one rule: refuse only when no line is about the order; never add the refusal to an answer | `qwen3:1.7b` | 3, 5, 4 | copies the lines (11) |
| e4 | none | `qwen3:4b-instruct-2507-q4_K_M` | 5, 5, 4 | missing terms; ids not in the lines (4) |
| e2 | none | `qwen3:4b` | 0, 0, 2 | not a measure: see below |

What we learned:

- **More rules made the small model worse.** Each rule we added was a
  right rule, and the score went down. A 1.7B model follows the words of
  the prompt, not their intent: told to end with "the recording does not
  show why", it added the sentence to every answer.
- **e1 changed six things at once.** It is the worst result, and we cannot
  say which rule did it. This is why rule 1 exists. e5 and e6 test two of
  the six rules alone: each one also makes the score worse.
- **The larger model is not better here.** The 4B instruct model refuses
  less, but it misses expected terms and cites ids that are not in the
  lines. At 3 runs, 14 against 17 of 36 is inside the noise.
- **`qwen3:4b` on this Ollama is a thinking model** (`ollama show`:
  thinking on by default, context 262144). With `think: false` it does not
  stop thinking: it writes its reasoning into the reply, with no
  `</think>` tag, and the 400-token limit cuts it before the answer. e2 measures the harness, not
  the model. Before you compare models, read one raw answer of each.

The holdout was not run for EXE12: no change was chosen over the control.
