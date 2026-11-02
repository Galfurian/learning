# Mental model: process mining

Numbers from the committed logs of this unit: `train` (200 simulated
orders), `holdout` (60), and the invented reference order `ref-order` with
its injected copies. All the data is simulated or invented (section 9).

## 1. A recipe is a model. A log is what happened.

```text
A recipe is a model. A log is what happened.
Process mining measures the distance between them, and the distance is the evidence.
```

The recipe says what must happen: the operations, their dependencies, the
fail branch. Compiled into a Petri net (EXE05), the gadget recipe has 12
transitions and 231 possible sequences up to 15 operations. The log says
what happened: 32 variants over 200 `train` orders. Conformance measures
the distance with event ids (EXE06, EXE07):

- distance 0: the order follows its recipe;
- a model move: the recipe has a step the order does not have (skipped);
- a log move: the order has a step the recipe does not have (extra).

A discovered model (EXE04) answers another question: "what does the log
look like?". It does not say what is right. Alpha fails on noise and on
incomplete logs; the inductive miner fits every trace and allows an order
with no board test. Neither replaces the recipe.

## 2. The case notion is a choice

The line logs what machines do; no event carries an order id. One gadget
order uses three pallets and two robots. Choose the case, and you choose
the errors:

| case | lost events | copied events | mixed orders |
|------|-------------|---------------|--------------|
| order | 0 | 0 (convergence 0) | no |
| pallet | 759 of 3,027 (no pallet) | 526 (convergence) | yes: ids are reused (divergence 125) |

The order is the case for "which recipe, where, did it conform". The
order case still has divergence 19, and it is correct: after a failed
check the covers come back on a new pallet. An object-centric log (EXE10)
keeps every object and leaves the choice to the question.

The order of each event is **inferred** by correlation rules (load bursts,
bay stays, pallet reuse; `orders.py`). Their thresholds (`JOIN_S` 3 s,
`ARRIVE_S` 15 s) are calibrated on the simulator, not on real data. On
`train`, 5,848 of 5,854 events get an order; the other 6 stay out (no
guess).

## 3. Abstraction: from missions to operations

`load_board` is two robot_a missions. `test_board` is a stay at the tester
bay and a test result. The abstraction (EXE02) turns 56 events of
`ref-order` into 21 entries. Every entry is `inferred`: the mapping is a
rule, not a reading.

The abstraction also hides things. A lost mission end (`gap`) or a copied
event (`duplicate`) does not change the operation sequence: on `train`,
token replay and alignments flag 0 of 3 gaps and 0 of 5 duplicates. These
are **data-quality** problems, not **control-flow** deviations. Check them
at the event level, before the abstraction.

Activities that match no recipe step stay as `unmapped:<activity>`. Token
replay skips them (as pm4py does); an alignment counts them as log moves.
The evidence lines leave them out of the moves and give them a coverage
line: "it matches no recipe operation, so conformance ignores it".

## 4. Recipe identity is inferred until the divergence

`gadget` and `parts_test` share their first four operations. On that
prefix, nothing in the log tells them apart, and a person at the line
cannot tell either. The honest answer is "gadget or parts_test, not decided
yet; check_covers would decide gadget, mill_part would decide parts_test"
(`inferred`).

On `ref-order` the recipe is decided at t=380.5 s, at the start of
`check_covers` [e17, e18, e19, e29]: only gadget has a QC check after the
loads. From that event on, the recipe is `derived` and cites the event. On
`train`, 185 of 200 whole orders are decided, all on the true recipe; 13
fit no recipe (deviations) and 2 stay on the shared prefix.

## 5. Running is not a deviation

`ref-order` ends while `engrave_gadget` runs. Replayed as a complete trace
it has fitness 0.923 and two model moves (engrave, deliver). Replayed as a
running case (`complete=False`) it has fitness 1.0 and cost 0. An
unfinished order is not a wrong order.

But the control flow cannot tell "not yet" from "stuck": `ref-stuck`
(engrave open for 482 s) gives the same replay as `ref-order`. The time
tells them apart (section 7).

## 6. The fail branch is not a deviation

A failed covers check, then `bin_covers`, `reload_covers`, and
`check_covers` again: this is in the recipe. The alignment has it as sync
moves, at cost 0. On `train`, `check_covers` failed 19 of 120 times (16%).
"Is a failed check normal?" has a measured answer: it happens, and the
recipe plans for it.

## 7. Unusual is a comparison with a baseline, not a cause

With a start and a complete per operation, the `train` log gives
baselines. `engrave_gadget`: p50 148 s, p95 216 s (nominal 150 s).

| order | now | engrave open for | verdict |
|-------|-----|------------------|---------|
| ref-order | 1118 s | 200 s | running: within the p95 |
| ref-stuck | 1400 s | 482 s | unusual: longer than the p95 |

The nominal time is shown next to the baseline, not used alone:
`reserve_pallet` has a nominal 10 s and a measured p50 of 51 s, because its
evidence (a bay stay) holds the wait for the load. The longest wait (p95)
is before `build_bricks`, 598 s: orders share the assembly cell.

"Unusual" says where and how much. It does not say why. The log has no
line that gives a cause, so every set of evidence lines ends with a
coverage line: "the recording does not show why". The abstention of the
generator is guided by that line; it does not find the gap by itself. The
cause is the next unit (09).

## 8. The data is simulated, and why

The real line gave one gadget order (three pallets, a failed covers check,
no delivery). One order is not enough to discover a process, and the
repository is public. So:

- `recipes.yaml` holds invented recipes with the shape of a real recipe
  ConfigMap; the nominal times are rounded measured times;
- `train` and `holdout` are play-outs of the recipes (seeded,
  deterministic) with concurrency, shared resources, reused pallet ids, a
  fail probability and injected deviations; the true order of each event is
  in a separate truth file;
- `ref-order` has the shape of the real order, with invented ids and
  rounded times; its copies inject one fault each.

The numbers in this unit measure the method on simulated data. They do not
measure the real line.

## 9. What this unit does not do: next steps

- **Heuristic miner by hand:** the dependency measure on the DFG, with a
  threshold, tolerates the noise that breaks Alpha.
- **Inductive miner by hand:** the recursive cuts (sequence, choice,
  parallel, loop) on the DFG; this unit uses pm4py's only for comparison.
- **Declare:** declarative constraints ("every `bin_covers` is followed by
  `reload_covers`") instead of a net; good for loose processes.
- **Stochastic nets:** probabilities on the choices and durations on the
  transitions, so "unusual" becomes a probability, not a p95 cut.
- **Root cause (unit 09):** why an operation is slow, from the signals
  around it.
