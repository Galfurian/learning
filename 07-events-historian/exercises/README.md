# Exercises

Each exercise is one folder: `README.md` (task, concept, runs), `exeNN.py`
(the file you edit, with a TODO), `check.py` (verifies it without a model or
network). Run from the unit folder (`07-events-historian/`).

| #  | Folder | You write | Concept |
|----|--------|-----------|---------|
| 00 | [exe00-demo](exe00-demo/) | nothing | one pallet from value changes to a cited answer |
| 01 | [exe01-catalog](exe01-catalog/) | `select_nodes(nodes)` | subscribe only to what moves |
| 02 | [exe02-event-time](exe02-event-time/) | `place(wall, polls)` | event time from the playback position, with bounds |
| 03 | [exe03-clean](exe03-clean/) | `clean(changes)` | what is a real change |
| 04 | [exe04-rules](exe04-rules/) | `derive_missions(changes)` | signals to events, with evidence |
| 05 | [exe05-cases](exe05-cases/) | `assign_cases(events)` | pallet + product cycle; inferred links |
| 06 | [exe06-chain](exe06-chain/) | `chain(events, case_id)` | the evidence chain of one case |
| 07 | [exe07-answer](exe07-answer/) | `SYSTEM_PROMPT`, `messages(...)` | the generator cites the evidence |
| 08 | [exe08-benchmark](exe08-benchmark/) | nothing | dev and holdout, stage by stage |

```bash
uv run python exercises/exe03-clean/check.py                            # verify, no model, no network
uv run python exercises/exe03-clean/exe03.py                            # on the cached recording
uv run python exercises/exe03-clean/exe03.py --fixture                  # on the invented fixture
uv run python exercises/exe03-clean/check.py exercises/solutions/exe03.py
```

Options shared by the exercises: `--trace` (default `lab-session`, a logical alias),
`--speed` (1 or 10, the recording to read), `--fixture`.

## Extra

1. **A routing rule.** Add a causal rule for "a passed QC check, then the
   assembly bay". Which dev answer changes? Is the rule observed, derived or
   inferred?
2. **The loading side.** Correlate robot_a's missions at the load/unload bay
   to the pallet there, as cases.py does for the QC bay.
3. **A historian query tool.** Write a typed function "events of a resource
   between two times" over `historian.py` and let the generator call it
   (unit 01).
