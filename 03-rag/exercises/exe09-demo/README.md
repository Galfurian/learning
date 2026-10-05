# EXE09 — A plant's manuals: larger than the context

This one is a **demo**: everything is already written. Read it, run it, and
compare the runs.

The plant has 40 invented machines: eight types (laser cutter, 3D printer,
reflow oven, conveyor, CNC mill, robot arm, vision station, packaging
sealer), five of each. Their manuals come from one generator
([plant/build.py](plant/build.py)), so the five manuals of one type are
near-duplicates: same sections, same sentences, different values, error
codes and part numbers (`PN-X1V-991-B`, `PN-X2V-991-B`, …). Together they
are 480 sections, about 30,600 estimated tokens. The generator's context
window is 8192 tokens.

## The three modes

```text
--mode stuff     the APP puts as many whole manuals as fit in the context, then asks
--mode pipeline  the APP retrieves the top k chunks, then the generator answers (EXE01–EXE07)
--mode tool      the generator calls the MCP tool search_manuals, when and how it wants
```

- `stuff` is unit 01 EXE05 at scale: the host attaches content up front,
  whether the question needs it or not. Only 84 of the 480 sections fit.
- `tool` is close to unit 01 EXE06: the model decides what to load. There it
  chose a resource by name; here it writes a search query.
- `pipeline` is the system you built in EXE01–EXE07.

## Actors

`stuff` and `pipeline` have the three actors of the unit. `tool` has four:
the APP is the MCP host, the GENERATIVE MODEL asks for `search_manuals`, the
MCP SERVER ([manual_server.py](manual_server.py)) runs the retrieval, and the
EMBEDDING MODEL works inside the server.

```bash
uv run python exercises/exe09-demo/exe09.py --mode tool --verbose --case 1
```

shows `APP -> GENERATIVE MODEL`, the `tool_calls` in its response, `APP ->
MCP SERVER · tools/call search_manuals`, the excerpts, and the final call.

## Dev vs holdout

[config.py](config.py) holds the settings of the final system, each with the
dev-set measurement that chose it: chunk size 60, k = 3, budget 1500, no
score threshold, semantic retrieval. The 20 holdout questions
(`data/plant/holdout.json`) were written and committed before the first
EXE09 run, and not changed after it.

The limit: the same author wrote the corpus generator and the questions. The
holdout is a discipline, not a guarantee.

## Results

`--eval` scores each answer by code, on the 20 holdout questions (17 with an
answer, 3 without), with `embeddinggemma` and `qwen3:1.7b`:

| mode                         | evidence seen | facts | citations ok | avg prompt tokens | avg s |
|------------------------------|---------------|-------|--------------|-------------------|-------|
| stuff                        | 0/17          | 3/20  | 2/20         | 4098              | 48.8  |
| pipeline (config: semantic)  | 15/17         | 16/20 | 20/20        | 414               | 5.5   |
| pipeline, `--retriever hybrid` | 17/17       | 17/20 | 20/20        | 398               | 4.9   |
| tool                         | 12/17         | 13/20 | 16/20        | 644               | 11.1  |

- **evidence seen**: a chunk of a relevant section reached the generator.
- **facts**: the expected value is in the answer, or the answer refuses a
  no-answer question. It is a coarse check: "Check the air pressure is below
  2.5 bar" fails it because it does not say "supply hose".
- **citations ok**: the cited ids are among the chunks the generator saw.
- **avg prompt tokens**: for `tool`, the final generator call only.

### stuff

The 84 sections that fit are the first manuals in file order (the conveyors
and two laser cutters). No holdout question is about them, so the right
page never reached the generator: evidence 0/17. The generator answered
anyway, with invented values ("The nominal spindle speed of the Heron M-78
is 7800 RPM"; the manual says 17000), and it did not refuse the three
no-answer questions. Each question cost about 4100 prompt tokens and 49 s on
CPU.

### pipeline

The semantic pipeline found the right section for 15 of 17 questions. The
two misses are the questions that contain only a part number: "What is
PN-X3Q-919-A?" and "What is part PN-X4Y-919-B?". Forty spare-parts lists
look alike, and the embedding cannot keep `PN-X3Q-919-A` apart from
`PN-X3Q-991-A` or `PN-X2Q-919-A`. The generator then replied "Not in the
manuals", which is the right behavior for what it was given. It refused all
three no-answer questions.

This is the case of EXE07, and the dev set was too small to show it: there,
semantic search found every part number, so `config.py` says "semantic".

### pipeline with hybrid retrieval

```bash
uv run python exercises/exe09-demo/exe09.py --mode pipeline --retriever hybrid --eval
```

This run is a reported comparison, not a change of the configuration. Hybrid
retrieval found the right section for all 17 questions: BM25 matches the
exact token `pn-x4y-919-b`. Then the generator failed on the same two
questions in a new way: "PN-X4Y-919-B: heater element [sealer4-parts-1]".
The heater element is `PN-X4Y-919-A`, the line above. Retrieval succeeded;
the generator read the wrong line of a list of near-identical codes. In
EXE08 terms, the failure moved from RETRIEVAL to GENERATION.

### tool

The model wrote good queries ("Ibis R-82 error E-6120", "Heron M-78 nominal
spindle speed") and searched once per question. It found the right section
for 12 of 17 questions, fewer than the pipeline:

- for part numbers it searched the bare code, and got the wrong spare-parts
  list ("PN-X4Y-919-B is mentioned as a lens cover. [vision4-parts-1]");
- for symptoms in other words it searched the symptom, not the cause
  ("Kestrel LX-57 parts morning evening shift"), and the warm-up sentence
  did not come back;
- it often wrote the excerpt id in prose instead of in brackets, so 4 of 20
  answers failed the citation check.

It also costs more: two generator calls per question and 11 s, against one
call and 5.5 s. The 644 prompt tokens in the table count only the final call
(which already holds the first call's messages and the excerpts); the first
call reads its prompt too, so the total input is larger. Giving the model the decision of
when and how to search adds a step that can fail.

## Run it yourself

```bash
uv run python exercises/exe09-demo/check.py
uv run python exercises/exe09-demo/exe09.py --inspect
uv run python exercises/exe09-demo/exe09.py --mode pipeline --case 5
uv run python exercises/exe09-demo/exe09.py --mode tool --verbose --case 1
uv run python exercises/exe09-demo/exe09.py --mode stuff --eval      # about 16 minutes on CPU
uv run python exercises/exe09-demo/exe09.py --mode pipeline --eval   # about 2 minutes
uv run python exercises/exe09-demo/exe09.py --mode tool --eval       # about 4 minutes
uv run python exercises/exe09-demo/exe09.py --compare
```

The first run embeds the plant (600 chunks, about 80 s on CPU) into the
cache. `--compare` prints the table of the saved `--eval` runs, from
`.cache/measurements/`.
