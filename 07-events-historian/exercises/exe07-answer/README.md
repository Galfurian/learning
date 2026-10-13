# EXE07 — The generator cites the evidence

**Concept:** the generator reads numbered evidence lines, never raw signals.
It must cite ids, say "inferred" for inferred links, take a "why" only from a
cause line, and refuse when the lines do not answer. Code checks all of it.

## Task

Write `SYSTEM_PROMPT` and `messages(question, chain)` in `exe07.py`.

```bash
uv run python exercises/exe07-answer/check.py
uv run python exercises/exe07-answer/exe07.py
uv run python exercises/exe07-answer/exe07.py --case p8#1 --question "Why did pallet 8 go to the assembly bay?"
```

## What to look at

- The panel "What the generator reads": story lines, the cause line, the
  coverage line.
- Measured with the reference prompt: "Why did robot_b throw covers in the
  bin?" → the failed QC check and the rework, citing `[e469]` and the
  missions, with "inferred".
- The first prompt without "write in your own words" made `qwen3:1.7b` copy
  the lines and then refuse; with raw per-event lines (before the story) it
  cited ids that did not exist. The checks caught both.
