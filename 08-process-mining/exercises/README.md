# Exercises

Each exercise is one folder: `README.md` (task, concept, runs), `exeNN.py`
(the file you edit, with a TODO), `check.py` (verifies it on small inline
data, and against pm4py where pm4py has the same algorithm). No model and
no network. EXE11 and EXE12 are the exceptions: they need Ollama. Run from
the unit folder (`08-process-mining/`).

| #  | Folder | You write | Concept |
|----|--------|-----------|---------|
| 00 | [exe00-demo](exe00-demo/) | nothing | "the recipe stopped": events, log, model, conformance, timing, cited answer |
| 01 | [exe01-event-log](exe01-event-log/) | `to_log(entries, case_notion)` | the case notion: order or pallet; lost and copied events |
| 02 | [exe02-abstraction](exe02-abstraction/) | `match_operations(case, units)` | missions and events become operations with a start and a complete |
| 03 | [exe03-dfg](exe03-dfg/) | `dfg(traces)` | directly-follows graph, variants, rare paths |
| 04 | [exe04-alpha](exe04-alpha/) | `alpha(traces)` | discovery and its limits; the inductive miner (pm4py) for comparison |
| 05 | [exe05-recipe-net](exe05-recipe-net/) | `compile_recipe(recipe)` | the recipe as a Petri net (normative model), play-out |
| 06 | [exe06-token-replay](exe06-token-replay/) | `token_replay(net, trace)` | fitness; running is not a deviation |
| 07 | [exe07-alignments](exe07-alignments/) | `align(net, trace)` | skipped and extra steps, with event ids |
| 08 | [exe08-performance](exe08-performance/) | `performance(traces)` | service and waiting times, p50/p95 baselines, "unusual" |
| 09 | [exe09-monitoring](exe09-monitoring/) | `candidates(prefix, nets)` | which recipe, decided only at the divergence |
| 10 | [exe10-ocel](exe10-ocel/) | `ocel(entries)`, `flattening_errors(o, type)` | object-centric log; convergence and divergence |
| 11 | [exe11-benchmark](exe11-benchmark/) | nothing | dev and holdout questions, first failing stage |
| 12 | [exe12-generator](exe12-generator/) | `SYSTEM_PROMPT` | improve the answers and prove it: one change, 3 runs, holdout once |

```bash
uv run python exercises/exe06-token-replay/check.py                             # verify, no model, no network
uv run python exercises/exe06-token-replay/exe06.py                             # on the committed logs
uv run python exercises/exe06-token-replay/exe06.py --log holdout               # another committed log
uv run python exercises/exe06-token-replay/check.py exercises/solutions/exe06.py
```

`--log` takes a committed log name (`train`, `holdout`, `ref-order`,
`ref-stuck`, `ref-skip-check`, `ref-no-end`, `ref-prefix`) or the path of a
`.jsonl` file in the same shape. Each runner shows your result next to the
reference result, and says if they are the same.

The solutions in `solutions/` call the unit's own modules (`src/pmlab/`):
read those for the full code. Do not commit your `exeNN.py`.

## Extra

1. **The heuristic miner by hand.** Compute the dependency measure
   `(|a>b| − |b>a|) / (|a>b| + |b>a| + 1)` from your DFG and keep the edges
   over a threshold. Does it survive the noise that breaks Alpha on
   brick_demo?
2. **A data-quality check.** EXE06 and EXE07 do not see the injected gaps
   and duplicates. Write a check at the event level (a mission start with
   no end, two equal events) and count what it finds on `train`.
3. **A Declare constraint.** Write "every `bin_covers` is followed, later,
   by `reload_covers`" (the Declare `response` template) as a rule over
   traces, with no Petri net. How many `train` orders break it?
