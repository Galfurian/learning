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

## Run, one step at a time

Each step runs one thing and asks one question. The "Measured" lines come
from runs with the reference solution (`embeddinggemma`, k = 3,
`qwen3:1.7b`); your answers can differ, because generation is not
deterministic.

### 1. Two near-duplicate chunks

```bash
uv run python exercises/exe06-generation/exe06.py --case 8
```

"What is the highest temperature in the lead-free solder profile?" Look at
the hits table: which chunk is rank 1, the leaded or the lead-free profile?
Then read the answer panel: which value did the generator give, and which
id did it cite?

The lesson: retrieval put the right chunk in the context, but not first.
From here on, picking the right one of two similar chunks is the
generator's job.

Measured: leaded first (0.614), lead-free second (0.544); the answer was 245
°C, citing `rf9-profile-1`.

### 2. A question the manuals cannot answer

```bash
uv run python exercises/exe06-generation/exe06.py --case 23
```

"What is the warranty period of the conveyor?" EXE05 showed that this
question passes the threshold with three irrelevant chunks. Look at the
answer panel: did the generator reply exactly "Not in the manuals."? Look at
the subtitle: your `check_citations` should say "citations ok", because a
clean refusal is a correct answer.

The lesson: the prompt's refusal rule is the second check, after the
threshold.

Measured: "Not in the manuals." for d23, d25 and d26.

### 3. What the generator really reads

```bash
uv run python exercises/exe06-generation/exe06.py --show-raw --case 3
```

The green panel is the exact text that goes into the model after Ollama
applies the chat template. Find your `SYSTEM_PROMPT`, the excerpts with
their `[id]` lines, and the question. Nothing else reaches the model: no
manual, no score, no other chunk.

### 4. The APP can decide not to call the generator

```bash
uv run python exercises/exe06-generation/exe06.py --budget 40 --case 3
```

A budget of 40 estimated tokens is smaller than any chunk. Look at the
context panel ("empty context (budget)") and at the answer panel ("The APP
abstained (budget); the generator was not called"). There is no generator
time in the subtitle, because there was no request.

### 5. The whole dev set

```bash
uv run python exercises/exe06-generation/exe06.py
```

This takes a few minutes. Read only the summary table at the end:

- `citations` is your `check_citations`;
- `facts` is a check by code that the library adds: the answer contains the
  expected value, or is a refusal for a no-answer question.

Look for the rows where the two columns disagree: `citations ok` but
`facts no`. Those answers cite a chunk from the context and still do not
answer. For each one, run it alone with `--case N` and check whether the
right chunk was in the context.

Measured: citations 26 of 26, facts 21 of 26. All five failures had the
right chunk in the context:

- d01 "Can I cut a vinyl sheet?" and d02 "Is it safe to engrave PVC
  signs?": the materials section came first, and the generator replied "Not
  in the manuals". The manual says "Never cut PVC or vinyl".
- d11 (tombstoning): refused, with the troubleshooting chunk in the context.
- d09 and d10: the answer repeats the question ("The extruder makes a
  clicking noise. [p3-troubleshooting-1]"). The citation is valid; there is
  no answer.

The lesson: a valid citation does not mean a useful answer. The next
section shows that it does not even mean a supported one.

### 6. Optional: a larger generator

```bash
ollama stop qwen3:1.7b
uv run python exercises/exe06-generation/exe06.py --model qwen3:4b --case 1
uv run python exercises/exe06-generation/exe06.py --model qwen3:4b --case 8
ollama stop qwen3:4b
```

Compare with the `qwen3:1.7b` answers to d01 and d08, and look at the time
in the subtitle.

Measured: `qwen3:4b` answered d01 correctly, but took 37–137 s per question
on CPU instead of 2–7 s. It ignores `"think": false` and writes its
reasoning before `</think>`; the client moves that part out of the answer.
For d08 its whole answer was `[rf9-profile-1]`: a valid citation, and no
value. A larger model is not a cleaner answer.

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
