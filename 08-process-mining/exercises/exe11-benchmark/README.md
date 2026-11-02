# EXE11 — The benchmark

Solved. Every question goes through the whole pipeline: log → unit 08 rules
→ orders → abstraction → **selection** (the order and the time named in the
question) → **mining** (recipe candidates, open operations, alignment,
baselines) → evidence lines → **answer**. The first failing stage:

```text
SELECTION -> MINING -> GENERATION -> NONE
```

```bash
uv run python exercises/exe11-benchmark/exe11.py --set dev
uv run python exercises/exe11-benchmark/exe11.py --set dev --echo  # no model: the lines are the answer
uv run python exercises/exe11-benchmark/exe11.py --set holdout     # once, at the end
```

`--echo` is the baseline of no model. A generator that does not beat it
adds nothing.

The questions: 12 dev (simulated `train` orders, `ref-order`, `ref-stuck`,
and `ref-prefix`, a copy cut before the divergence) and 8 holdout
(simulated `holdout` orders, and two other injected copies of the reference
order: `ref-skip-check`, a skipped check, and `ref-no-end`, a missing
mission end). Types: which recipe, where is it, stopped or slow,
conformance, normal or not, abstention. The holdout was committed before
the first run.

The data is simulated and invented. There is no real order in the
repository: the repository is public, and one real order is too few to
discover a process. The reference order has the shape of one real order of
the lab line (three pallets, a failed covers check, no delivery), with
invented ids and rounded times.

## Results

Each answer passes checks by code: the right order and time, the gold
event ids in the evidence lines, valid citations, "probably" where a line is
inferred, and the question's `expect` rubric (the facts that must appear
and those that must not).

Abstention here is **evidence-guided**: every set of evidence lines ends
with a coverage line that says the recording does not show why. A right
"why" answer repeats that line; it does not find the gap by itself.

## Measured runs

Measured on 2026-11-02 on the local CPU, `qwen3:1.7b`, `max_tokens` 400,
three runs per set. With the current scorer:

| set | echo (no model) | `qwen3:1.7b`, right per run |
|-----|-----------------|-----------------------------|
| dev (12) | 1 | 6, 5, 5 / 5, 6, 6 (two days) |
| holdout (8) | 0 | 2, 2, 3 |

SELECTION and MINING never fail; every failure is at GENERATION. Before
the scorer audit, the echo baseline scored 11 of 12 on dev: the rubric
checked the facts, not the answer. The unit README, section 5, has the
audit, the scorer changes (one of them on the holdout, after it was seen)
and the model errors one by one.

The raw outputs are not committed. Run `exe11.py --set dev` and
`--set holdout` to measure again.
