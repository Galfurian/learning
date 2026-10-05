# EXE06 — A grounded answer, checked by code

**Concept:** the generator writes the answer, but the APP decides what it
reads and checks what it wrote. The prompt asks for citations, and code
verifies them.

## Task

1. Write `SYSTEM_PROMPT` in `exe06.py`: use only the excerpts; cite the id of
   every excerpt used, in square brackets; reply exactly `REFUSAL` when the
   excerpts do not contain the answer.
2. Implement `check_citations(answer, context_ids)`. The comment in the file
   lists the four outcomes. `cited_ids()` reads every id, also several ids in
   one bracket (`[lx40-cooling-1, p3-temps-1]`).

```bash
uv run python exercises/exe06-generation/check.py
```

## Run

```bash
uv run python exercises/exe06-generation/exe06.py --case 8
uv run python exercises/exe06-generation/exe06.py --case 23
uv run python exercises/exe06-generation/exe06.py
uv run python exercises/exe06-generation/exe06.py --show-raw --case 3
uv run python exercises/exe06-generation/exe06.py --budget 40 --case 3
ollama stop qwen3:1.7b
uv run python exercises/exe06-generation/exe06.py --model qwen3:4b --case 8
ollama stop qwen3:4b
```

The full run ends with a summary table. `citations` is your check. `facts`
is a check by code that the library adds: the answer contains the expected
value (or is a refusal, for a no-answer question).

## What to observe

Measured with the reference solution (`embeddinggemma`, k = 3,
`qwen3:1.7b`):

- **Citations: 26 of 26 pass. Facts: 21 of 26 pass.** Every failure on
  `facts` happened with the right chunk in the context:
  - d01 "Can I cut a vinyl sheet?" and d02 "Is it safe to engrave PVC
    signs?" — the materials section was retrieved first, and the generator
    replied "Not in the manuals". The manual says "Never cut PVC or vinyl".
  - d11 (tombstoning) — refused, with the troubleshooting chunk in the
    context.
  - d09 and d10 — the answer repeats the question ("The extruder makes a
    clicking noise. [p3-troubleshooting-1]"). The citation is valid; there is
    no answer.
- **d08, the lead-free peak.** The leaded profile ranks first in the
  context, the lead-free one second. `qwen3:1.7b` picked the right one: 245
  °C.
- **No-answer questions.** The generator refused all four, also d23, d25 and
  d26, which pass the EXE05 threshold with three irrelevant chunks.
- **The budget.** `--budget 40 --case 3`: no chunk fits, the context is empty,
  and the APP abstains ("The APP abstained (budget)") without calling the
  generator.
- **A larger model is not a cleaner answer.** `qwen3:4b` answers d01 and d09
  correctly, and for d10 it gives the cause (a clogged nozzle) but not the
  remedy. It takes 37–137 s per question on CPU instead of 2–7 s. It
  also ignores `"think": false` and writes its reasoning before
  `</think>`; the client moves that part out of the answer. For d08 its
  whole answer was `[rf9-profile-1]`: a valid citation, and no value.

## Citation exists ≠ citation supports the claim

`recorded.json` is a real answer from the run above (d18):

```text
question  What is PN-X7S-919-A?
context   rf9-parts-1, p3-parts-1, lx40-parts-1
answer    PN-X7S-919-A is a convection fan motor. [p3-parts-1]
```

The answer is right, but `p3-parts-1` is the 3D printer's spare-parts list,
and it does not contain PN-X7S-919-A. The fact comes from `rf9-parts-1`,
which was also in the context. The cited id exists and is in the context, so
your `check_citations` accepts it. The check proves it with its last line.

`check_citations` can prove that a citation exists. It cannot prove that the
cited text supports the claim. This unit does not solve that automatically.
EXE08 counts such an answer as a GENERATION failure, and the extras in
`exercises/README.md` try a decision-model check.
