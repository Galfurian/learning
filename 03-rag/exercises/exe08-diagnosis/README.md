# EXE08 — Which stage failed?

**Concept:** a wrong answer says nothing about where the pipeline broke.
Each trace records what every stage produced, so you can name the first
stage that failed, with a rule, not an opinion.

The 10 traces in `traces/` come from real runs of `exe00.py --record` on the
dev set: three settings (the default, `--fake-embed`, `--min-score 0.45`),
then a person read each answer and wrote the labels.

## The rule

```text
answerable question:
  1. no hit from a relevant section                        -> RETRIEVAL
  2. relevant hit, but no relevant chunk in the context    -> CONTEXT
  3. relevant chunk in context, and labels.answer_correct
     is false OR labels.supported is false                 -> GENERATION
  4. otherwise                                             -> NONE
no-answer question (relevant == []):
  refusal (abstained, or the answer contains "Not in the manuals") -> NONE
  any other answer                                                 -> GENERATION
```

The order matters. When retrieval misses, the answer is wrong whatever the
generator does, so the first failure is RETRIEVAL even if the generator then
refuses correctly.

No-answer questions skip rules 1 and 2. EXE05 showed that a score threshold
cannot keep every irrelevant chunk out, so irrelevant chunks in the context
are expected, and the generator's refusal is the last check.

## The labels

`answer_correct` and `supported` were written by a person who read the
answer and the cited chunks. `supported` is false when the cited chunk does
not state the claim, even if the claim is right. For a refusal there is no
claim, so `supported` is `null`.

`diagnose` does not judge text. It applies the order to the labels. This is
the line between what code can check and what needs a person (or, in the
extras, a decision model).

## Task

1. Open `traces/t03-d09-threshold.json` and `traces/t06-d18-default.json`.
   Find the hits, the context and the labels, and diagnose them by hand.
2. Implement `diagnose(trace)` in `exe08.py`.

```bash
uv run python exercises/exe08-diagnosis/check.py
uv run python exercises/exe08-diagnosis/exe08.py
```

The check runs 9 synthetic cases, then the 10 recorded traces.

## What to observe

| trace                | stage      | what happened |
|----------------------|------------|---------------|
| t01-d11-fake         | RETRIEVAL  | The FakeEmbedder found no tombstoning chunk: "tiny resistors lift up" shares no word with the manual. |
| t02-d07-fake         | RETRIEVAL  | `p3-temps` was rank 4, outside k = 3. |
| t03-d09-threshold    | CONTEXT    | `p3-bed` was the top hit at 0.419, below `--min-score 0.45`: the APP abstained. |
| t04-d18-threshold    | CONTEXT    | `rf9-parts` was the top hit at 0.349, below the threshold. |
| t05-d01-default      | GENERATION | "Never cut PVC or vinyl" was the first chunk; the generator said the manual does not mention vinyl. |
| t06-d18-default      | GENERATION | The right answer, citing the printer's parts list instead of the oven's (the EXE06 recorded case). |
| t07-d10-default      | GENERATION | The answer repeats the question, with a valid citation. |
| t08-d08-default      | NONE       | Leaded first, lead-free second: the generator picked the right one. |
| t09-d03-default      | NONE       | 15–22 °C, cited from `lx40-cooling-1`. |
| t10-d23-default      | NONE       | No warranty in any manual; three irrelevant chunks; the generator refused. |

- **Three GENERATION failures out of three had the right chunk in the
  context.** Retrieval did its job; the answer still failed. Without the
  trace, these would look like retrieval problems.
- **t08 and t06 are the same situation.** In both, a near-duplicate chunk
  (the leaded profile, another machine's parts list) sits next to the right
  one. In t08 the generator chose right. In t06 it chose the right fact and
  cited the wrong chunk.
- **The two CONTEXT traces are the threshold's cost.** The same threshold
  that would refuse a no-answer question also refused these two answerable
  questions. EXE05's table counted that cost before you chose.
- **No recorded no-answer question was answered anyway.** In every dev run,
  `qwen3:1.7b` refused the four no-answer questions. The synthetic cases in
  `check.py` cover that branch of the rule.
