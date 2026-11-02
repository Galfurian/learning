# EXE00 — "The recipe stopped": from low-level events to a cited answer

Solved. Read it, run it, and look at each stage.

```bash
uv run python exercises/exe00-demo/exe00.py --no-model    # the evidence lines only, no Ollama
uv run python exercises/exe00-demo/exe00.py               # with the generator
```

The default log is `ref-stuck`: a copy of the invented reference order, with
the end of `engrave_gadget` removed (an injected fault). The question comes
at t=1400 s.

## What to look at

1. **The first line** names the log and its injected fault.
2. **The stage table.** Measured: 55 low-level events → 56 after the unit 08
   rules (the mill program start becomes an event) → 56 events in one order
   → 21 log entries (a start and a complete per operation).
3. **The log of `order:1`.** Each operation cites the low-level events it
   comes from. `engrave_gadget` has a start at t=918 s and no complete.
4. **The evidence lines**, measured:

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

   Line 1 is the recipe. Before t=380.5 s the order can be `gadget` or
   `parts_test`: the two recipes share their first steps. Line 2 is the
   position and the timing. Line 4 is the fail branch: it is in the recipe,
   so it is not a deviation. Line 6 is the coverage line: no line gives a
   cause, so the answer must say that the recording does not show why.
5. **The answer** cites ids like `[e54]`. The subtitle says if every cited id
   is in the evidence lines.

The same question on `ref-order` at its last event gets a different right
answer:

```bash
uv run python exercises/exe00-demo/exe00.py --no-model --log ref-order
```

`engrave_gadget` is open for 200 s, within the p95 (216.5 s): the order is
still running. Nothing is stopped.

## Measured runs

Measured on 2026-11-02, local CPU, `qwen3:1.7b`: the generator replied
"Not in the recording." (refused, 6.6 s), although lines 1 to 4 answer
where the order is and that its timing is unusual. A 1.7B model on CPU
reads the "no cause" coverage line as "no answer". This is a GENERATION
failure: the evidence was right. The EXE11 benchmark measures how often it
happens.
