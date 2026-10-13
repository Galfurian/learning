# EXE04 — Signals to events

**Concept:** an event is a rule over changes, with its evidence (the change
ids) and its claim kind. A mission start is one change read as it is
(*observed*). A failed QC check is a rule over three changes: the check
mission started, it ended, and the fault counter moved (*derived*, in
`rules.py`).

## Task

Implement `derive_missions(changes)`: missions and destinations.

```bash
uv run python exercises/exe04-rules/check.py
uv run python exercises/exe04-rules/exe04.py
```

## What to look at

Measured: 29 missions started and ended, 19 destinations assigned and
cleared; the same events and evidence as the reference.

Then read `_qc_checks` in `src/evlab/rules.py`: the result of a check is not
one signal. The fault counter, the result flag and the check counter can
arrive before or after the end of the mission; the rule reads a window, and
says `check_result_unknown` when none of them moved.
