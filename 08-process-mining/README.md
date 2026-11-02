# 08 — Process mining

Goal: from the low-level events of a production line, find the process.
Which recipe does an order follow? Where is it now? Did it follow the
recipe? Is its timing usual? Build the standard process mining steps by
hand (event log, discovery, conformance, performance, online monitoring,
object-centric logs), and compare each one with pm4py, the standard
library.

The central message of this unit:

```text
A recipe is a model. A log is what happened.
Process mining measures the distance between them, and the distance is the evidence.
```

This is the second unit of the plant assistant track. Unit 07 gives the
events; this unit gives the process. The unit depends on nothing outside
itself: no simulator, no unit 07 code, no recording. Every exercise, test
and benchmark question runs on files committed here.

## The data is simulated and invented

The real lab line gave one gadget order: three pallets, a failed covers
check, no delivery. One order is not enough to discover a process, and the
repository is public. So the unit uses:

- `src/pmlab/data/recipes.yaml`: three invented recipes (`gadget`,
  `parts_test`, `brick_demo`) with the shape of a real recipe ConfigMap,
  plus the low-level events that are evidence of each operation;
- `data/logs/train.jsonl` (200 orders) and `data/logs/holdout.jsonl` (60):
  seeded play-outs of the recipes, with orders that run at the same time,
  shared robots and bays, reused pallet ids, a fail branch and injected
  deviations. The true order of each event is in `<name>.truth.json`, not
  in the events;
- `data/orders/ref-order.jsonl`: one invented order with the shape of the
  real one, and copies of it with one injected fault each (`ref-stuck`,
  `ref-skip-check`, `ref-no-end`, `ref-prefix`).

The numbers below measure the method on this data, not the real line.

## What you will build

```text
LOW-LEVEL EVENTS  missions, bay stays, checks, cell and mill signals    events.py
   | unit 08 rules: mill program start/end; cell event -> pallet        rules.py
   | correlation: which order each event belongs to (INFERRED)          orders.py
   v
EVENT LOG   one entry per operation start and complete, with ids        abstraction.py, log.py
   | the case notion: order (main) or pallet; OCEL keeps both           ocel.py
   v
MODELS      discovered: directly-follows graph, Alpha                   dfg.py, alpha.py
            normative: the recipe compiled into a Petri net             compile.py, petri.py
   v
CONFORMANCE token replay (fitness), alignments (skipped, extra, ids)    replay.py, align.py
PERFORMANCE service and waiting times, p50/p95 baselines                performance.py
MONITORING  recipe candidates of a running order, open operations       monitor.py
   v
EVIDENCE    numbered lines with ids and claim kinds                     evidence.py
ANSWER      the generator cites event ids; code checks the citations    answer.py
```

Claim kinds follow unit 07: a recipe is `inferred` while two recipes still
fit, `derived` (with the deciding event id) after the divergence; a
`coverage` line says what the log does not show.

## Prerequisites

- Python 3.11+ and `uv`.
- Ollama with `qwen3:1.7b` for EXE00 (without `--no-model`), EXE11 and EXE12.
  Everything else runs offline, with no model.
- pm4py comes with `uv sync`. It is used in the tests, in the `check.py`
  files and in the EXE04 comparison only. No Graphviz: the models print as
  text tables.

## 0. Install

```bash
cd learning/08-process-mining
uv sync
uv run pytest
```

## 1. The question, end to end

```bash
uv run python exercises/exe00-demo/exe00.py --no-model
```

"The recipe stopped, I don't know why", asked at t=1400 s on `ref-stuck`.
Measured evidence lines:

```text
1. [e17, e18, e19, e29] order:1 follows recipe gadget: only gadget fits
   check_covers (start) at t=380.5 s (derived)
2. [e54, e55, e56] order:1 is at engrave_gadget: started at t=918 s, still
   open at t=1400 s, age 482 s; usual time p50 148.2 s, p95 216.5 s over the
   train log; nominal 150 s; unusual: longer than the p95 (derived)
3. [e4, e45] order:1 follows recipe gadget so far with no deviation
   (alignment cost 0) (derived)
4. [e17, e20, e21] order:1: check_covers failed once, then bin_covers and
   reload_covers ran: fail branch of the recipe: conformant (derived)
5. over the train log, check_covers failed 19 of 120 times (16%) (derived)
6. no line gives a cause: the recording does not show why an operation is
   slow or why a check failed (coverage)
```

The same question on `ref-order` at its last event (t=1118 s) has another
right answer: `engrave_gadget` is open for 200 s, within the p95. The order
is still running; nothing is stopped.

## 2. Regenerate the data (optional)

```bash
uv run python data/build.py                     # rewrites data/logs and data/orders, deterministic
uv run python scripts/simulate.py --orders 50 --seed 1 --out .cache/logs/demo.jsonl
uv run python exercises/exe08-performance/exe08.py --log .cache/logs/demo.jsonl
```

A test compares a fresh build with the committed files.

## 3. Read the code in this order

1. `events.py`, `recipes.py` and `data/recipes.yaml` (the contracts).
2. `simulate.py` (the play-out), `rules.py`, `orders.py` (correlation).
3. `abstraction.py`, `log.py`, `dfg.py`, `alpha.py`.
4. `petri.py`, `compile.py`, `replay.py`, `align.py`.
5. `performance.py`, `monitor.py`, `ocel.py`.
6. `evidence.py`, `answer.py`, `benchmark.py`.
7. `docs/mental-model.md`.

`client.py`, `ui.py`, `checks.py` are copies from unit 07. `reference.py`
is the only module that imports pm4py.

## 4. Write your own pieces

Continue with [exercises/README.md](exercises/README.md).

## 5. Measured runs

Measured on 2026-11-02 on the local CPU (Intel Core Ultra 9 185H, WSL),
`qwen3:1.7b` on Ollama, `max_tokens` 400, the unit's prompt. Three runs per
set, because the generator samples. One set takes less than one minute.

### First: what is a score worth?

The first measured runs gave 4, 7 and 4 of 12 on dev. Before we trusted
these numbers, we did two checks.

**A baseline with no model.** `exe11.py --echo` answers with the evidence
lines themselves (or the refusal, when no line names an event). It scored
**11 of 12 on dev and 7 of 8 on holdout**: better than the model. The
rubric checked that the facts were in the text, not that the text answered
the question. Now a verbatim copy of an evidence line of 40 characters or
more fails ("copies N evidence line(s) instead of answering"). The echo
baseline now scores **1 of 12 on dev and 0 of 8 on holdout**.

**An audit of every GENERATION failure.** We read each failing answer and
asked: is it the model, or is it the scorer? Scorer problems, fixed:

- Failures with no note. A refusal, or an answer that cites no gold event,
  failed in silence. Now each has a note.
- The line "follows recipe gadget with no deviation" had no ids, so no
  answer could cite it. Now it cites the first and the last aligned event.
- An answer that cites one id of a line counts as citing the line: a line
  is one statement.
- The rubric of d09 asked for "fail branch" literally; a right "it follows
  the recipe, no deviation" failed. The rubric of d10 asked for the same
  literal; "it is normal, 19 of 120" failed. Both now take synonyms.
- **h07 (holdout) got the same change as d10, after the holdout was seen.**
  It is the twin question of d10. We write it here because a holdout change
  after a run is a leak, even when it fixes the rubric.
- In the final review, the negative conformance rubrics (d08; h05 and h06
  on holdout) still took "no deviation" as a "deviat" match. "no
  deviation" is now in their "none" group. This makes them stricter; no
  saved answer changed its score.

Model errors, not changed (one example each):

- It repeats the problem statement and refuses: "The recipe stopped, I don't
  know why. [e17] Not in the recording." (d06, d07, h04).
- It appends "Not in the recording." to a right answer.
- It cites ids that are not in the lines (d11).
- It names one recipe while the order is not decided (h01), or says "not
  decided" and names no candidate (d01).
- It does not name the deviation (d08, h05, h06).
- It invents a cause: "the covers check failed because the fail branch was
  conformant" (d12, h08).

### The numbers, with the current scorer

| set | runs | right per run | first failing stage |
|-----|------|---------------|---------------------|
| echo, no model, dev (12) | 1 | 1 | GENERATION only |
| echo, no model, holdout (8) | 1 | 0 | GENERATION only |
| `qwen3:1.7b`, dev (12) | 6 (two days of 3) | 6, 5, 5 / 5, 6, 6 | GENERATION only |
| `qwen3:1.7b`, holdout (8) | 3 | 2, 2, 3 | GENERATION only |

- SELECTION and MINING never fail: the evidence lines always hold the gold
  events (evidence recall 1.00 in every run). The process mining part is
  right; the small generator is the weak part.
- The model beats the echo baseline: about 5.5 of 12 against 1.
- Questions that fail in every run: d06, d07, d08, d10 on dev; h01, h04,
  h05, h06, h07 on holdout. d12 passed 3 of 3 on one day and 0 of 3 on the
  other: one run is not a measure.

### Try to make it better: EXE12

We tried to improve the generator on dev, 3 runs each, with the unit's
prompt as the control (the dev row above). See
[exercises/exe12-generator](exercises/exe12-generator/). No change was
better. The holdout row above is the unit's prompt, so the holdout was not
run again.

The raw outputs are not committed. Run `exe11.py --set dev`,
`exe11.py --set dev --echo` and `exe12.py --baseline` to measure again.

## What the unit does not do

- No real recipe, no real order, no real names, ids or hosts.
- No cause: the unit says where an order is and how unusual its timing is,
  not why (unit 09).
- No heuristic or inductive miner by hand, no Declare, no stochastic nets:
  see the next steps in `docs/mental-model.md`.

## The key lesson

"The recipe stopped" is three questions with three kinds of answers. Which
recipe: inferred until the divergence, then derived from one event. Where:
the open operation, with the event that opened it. Stopped or slow: a
comparison with a measured baseline, and an honest "the recording does not
show why".
