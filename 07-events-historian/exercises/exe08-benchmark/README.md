# EXE08 — The benchmark

Solved. Every question goes through the whole pipeline: recording → clean →
events → cases → **selection** (the pallet named, or the resources named) →
chain → causes → **answer**. The first failing stage:

```text
SELECTION -> EVIDENCE -> GENERATION -> NONE
```

```bash
uv run python exercises/exe08-benchmark/exe08.py --set dev
uv run python exercises/exe08-benchmark/exe08.py --set holdout     # once, at the end
```

The holdout is a **derived recording**: the real one, transformed before
cleaning (pallets 7/8/9 → 17/18/19, the two robots swapped, pallet 18 fails
its check with a late rework, pallet 19 has a check with no result and an
assignment without movement). It tests the pipeline, not a copied table.

## Results

Each answer passes four checks by code: the right case or evidence, the gold
event ids in the evidence, valid citations (and "inferred" where a link is
inferred), and the question's `expect` rubric: the facts that must appear
(entities, times within a tolerance, failed or passed) and those that must
not, each as a group of synonyms.

Measured, three runs of each set (`qwen3:1.7b`, CPU; the generator samples,
so runs differ):

| set | questions | right (3 runs) | SELECTION | EVIDENCE | GENERATION |
|-----|-----------|----------------|-----------|----------|------------|
| dev | 12 | 7, 5, 8 | 0 | 0 | 5, 7, 4 |
| holdout | 7 | 3, 4, 4 | 1 | 0 | 3, 2, 2 |

- **The evidence is there:** evidence recall 1.00 on both sets. Every
  failure on dev is in the generator.
- **The generator is the noise:** the same question is right in one run and
  wrong in the next (d02, d03, d06, d08, d10, d11 changed between runs). A
  single run of 12 questions cannot rank two prompts; three runs show the
  spread.
- **Stable failures:** d01 and d05 (an answer that leaves out a stay or the
  QC bay), h04 (a time without its ids), h07 (a "why" with no rule, told as
  if the recording said it).
- **h06** asks about "the later QC check with no result" and names no
  pallet: the selector has nothing to start from. A question about an event
  needs another selector (unit 10, the router).

How the score changed while the unit was built, so you can read old notes:
the first scorer counted an answer right with the gold ids cited and no
check of its content (dev 9/12, holdout 4/7, one run). A word-for-word
rubric then failed right answers ("left at t=523" against "cleared"; dev
3/12). The factual rubric above, written from the gold answers, gives the
table.
