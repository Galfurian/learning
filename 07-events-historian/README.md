# 07 — Events and historian

Goal: turn the value changes of a production line into evidence that an
answer can cite. Connect to the line over OPC-UA, record what changes, derive
domain events with versioned rules, group them by pallet and product cycle,
and answer one question with a chain of event ids.

The central rule of this unit: **an answer about the line is only as good as
its evidence: which signal changed, when, and what that change means.**

This is the first unit of the plant assistant track. The line is a real lab
line, replayed by a simulator (ice-sim) with the same OPC-UA servers. The
repository knows only **logical names** (`robot_b.mission`,
`qc_station.last_result`, `conveyor.destination.bay4_2`); the real node ids
live in a local, git-ignored file.

## What you will build

```text
ice-sim worker (OPC-UA replay)              scripts/record.py, sim.py, collector.py
   | subscriptions to the mapped signals; playback position polled every 0.5 s
   v
CHANGES  (value, event time with bounds, arrival order)          records.py
   | clean: initial values, duplicates, replay restarts           rules.py
   v
EVENTS   mission started/ended, check failed/passed, destination   rules.py
   |     assigned/cleared, pallet entered/left a segment, alarm
   | cases: pallet + product cycle; QC and robot links INFERRED     cases.py
   v
CHAIN    one case in time order; a visit counts only if the pallet  chain.py
   |     left the loop; a story with ids
   | causal rules: "failed check + covers to the bin = rework"      causes.py
   v
ANSWER   the generator cites event ids; code checks the citations  answer.py
```

Every record keeps its **claim kind**: observed (one change read as it is),
derived (a rule over changes), inferred (a join the signals do not state),
confirmed (an operator, a later unit).

## Prerequisites

- Python 3.11+ and `uv`; Ollama with `qwen3:1.7b` (EXE00, EXE07, EXE08).
- For new recordings: the lab tailnet and `export ICE_SIM_URL=http://<host>:<port>`.
  Without them, every exercise except EXE01 runs on the cached recordings or
  on the invented fixture in `data/fixture/`; EXE01 reads the live catalog
  (its check runs offline).

## 0. Install

```bash
cd learning/07-events-historian
uv sync
uv run pytest
```

## 1. The local mapping and a recording (lab members only)

```bash
# .local/traces.json (git-ignored): {"lab-session": {"trace": "<trace id>"}}
# .local/patterns.json (git-ignored): for each logical signal, the end of its real path
uv run python scripts/build_mapping.py --trace lab-session            # -> .local/mapping.json
uv run python scripts/record.py --trace lab-session --speed 1         # about 19 min -> .cache/recordings/
uv run python data/holdout/build.py                                   # the derived holdout recording
```

One worker per run, decommissioned at the end, also on errors. The token
stays in memory. Real string values without a logical name are stored as
`unmapped:<hash>`.

## 2. Follow one pallet

```bash
uv run python exercises/exe00-demo/exe00.py
```

Measured on `lab-session` at speed 1: 2,258 value changes → 2,177
real changes → 1,323 events → 3 cases. Case `p7#1`:

```text
pallet 7 was at the load/unload bay from t=284 s to t=371 s (observed)
pallet 7 was at the QC bay from t=392 s to t=523 s (observed)
QC check failed (inferred link to the pallet)
robot_b: go_to_qc_bay, take_cover_top_from_pallet, take_cover_bottom_from_pallet,
         go_to_bin, drop_covers_in_bin, go_home (inferred link to the pallet)
cause (rule rework-after-failed-check v1): the QC check failed, then robot_b took the covers
      off pallet 7 and dropped them in the bin: a rework
```

## 3. Read the code in this order

1. `records.py` (the contracts), `mapping.py` (logical names).
2. `sim.py`, `collector.py` (recording), `recordings.py`, `source.py`.
3. `rules.py` (cleaning and signals to events), `cases.py` (cases and inferred links).
4. `historian.py` (SQLite, typed queries).
5. `chain.py`, `causes.py`, `answer.py`, `benchmark.py`.
6. `docs/mental-model.md`.

`client.py`, `ui.py`, `checks.py` are copies from unit 05.

## 4. Write your own pieces

Continue with [exercises/README.md](exercises/README.md).

## The key lesson

The signals rarely say what a person asks. "The QC check of pallet 7 failed"
is three things: a check mission, a fault counter that moved, and the pallet
that was at the QC bay at that time. Two of them are observed, one is
inferred, and the answer must say which is which.
