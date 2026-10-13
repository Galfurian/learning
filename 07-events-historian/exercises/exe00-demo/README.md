# EXE00 — One pallet, from value changes to a cited answer

Solved. Read it, run it, and look at each stage.

```bash
uv run python exercises/exe00-demo/exe00.py --no-model    # the evidence only
uv run python exercises/exe00-demo/exe00.py               # with the generator
```

## What to look at

1. **The first line** says the source: a cached recording at speed 1, or the
   invented fixture.
2. **The stage table.** Measured: 2,258 value changes → 2,177 real changes
   → 1,323 events → 3 cases (`p7#1`, `p8#1`, `p9#1`).
3. **The evidence of `p7#1`.** Two stays (load/unload bay, QC bay), both
   *observed*: the pallet left the loop while assigned. The QC check and
   robot_b's six missions are *inferred links to the pallet*: no signal names
   pallet 7 at the QC station or at the robot.
4. **The cause line:** rule `rework-after-failed-check v1`. The "why" comes
   from this rule, not from the model.
5. **The answer** cites ids like `[e469]`; the subtitle says whether every
   cited id exists in the evidence.

`--case p8#1 --question "Why did pallet 8 go to the assembly bay?"`: no rule
explains it, and the right answer says the recording does not show why.
