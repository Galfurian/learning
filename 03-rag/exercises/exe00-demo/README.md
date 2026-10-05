# EXE00 — The whole pipeline, solved

Nothing to write. Read the file, run it, and trace it. EXE01–EXE07 then
build each piece by hand.

## What runs

```text
DOCUMENTS ── chunk ── embed ── store vectors                      (once, cached)

QUESTION ── embed ── nearest chunks ── build context ── LLM ── answer with citations
```

Three actors share the work:

```text
EMBEDDING MODEL    text -> vector                                   (Ollama /api/embed)
APP CODE           vectors -> relevant chunks -> context -> checks  (exe00.py + src/raglab)
GENERATIVE MODEL   question + retrieved chunks -> answer            (Ollama /api/chat)
```

The embedding model never sees the question and the manuals together. The
generative model never sees the manuals: it reads only the chunks the APP
puts in the context.

The manuals are in `data/dev/manuals/`. They describe four invented
machines. If the generator already knew the answers from its training, a
correct answer would prove nothing about retrieval.

## Without a model

```bash
uv run python exercises/exe00-demo/check.py
uv run python exercises/exe00-demo/exe00.py --inspect
```

The check tests the APP code with fake hits: the context keeps the rank
order, and the citation check accepts or rejects answers. `--inspect` shows
the first 20 chunks and the system prompt. No model is called.

## With the models

```bash
uv run python exercises/exe00-demo/exe00.py --case 3
uv run python exercises/exe00-demo/exe00.py --verbose --case 3
uv run python exercises/exe00-demo/exe00.py --show-raw --case 3
```

The first run embeds the 43 chunks (about 6 s on CPU) and stores the vectors
in `.cache/embeddings/`. Later runs read them from the cache.

For question 3 ("The laser tube is overheating. What temperature should the
coolant be?"), the APP retrieves `lx40-cooling-1` first (score 0.657). The
answer is "The coolant should be between 15 and 22 °C. [lx40-cooling-1]".

`--verbose` shows every HTTP request:

- `APP -> EMBEDDING MODEL · POST /api/embed`: the question, with the
  `task: search result | query:` prefix. The response is 768 floats; the
  display shows 4 of them and the count.
- `APP -> GENERATIVE MODEL · POST /api/chat`: the system prompt, and one user
  message with the excerpts and the question.

`--show-raw` shows the exact text the generator reads, after Ollama applies
the chat template (`<|im_start|>system`, `<|im_start|>user`, ...). It uses
`_debug_render_only`, an undocumented Ollama debug field (tested on 0.35.0).

## Things to notice

**Retrieval and generation are two separate steps.** Run
`exe00.py --case 8` ("What is the highest temperature in the lead-free
solder profile?"). The **leaded** profile ranks first (0.614) and the
lead-free profile second (0.544). Retrieval still succeeded at k = 3: the
right chunk is in the context. The generator then picked the right chunk and
answered 245 °C. Whether the generator picks the right one of two
near-duplicate chunks is a separate question. EXE08 is built around it.

**No answer in the manuals.** Run
`exe00.py --question "What is the warranty period of the conveyor?"`. The
APP still retrieves three chunks: there is always a nearest chunk, even when
none is relevant (here the C-12 maintenance, tension and speed sections,
scores 0.39–0.46). The generator read them and replied "Not in the
manuals." The refusal comes from the prompt, not from the retrieval. EXE05
asks whether the APP can abstain before it calls the generator.

**A lexical baseline.** Run `exe00.py --fake-embed --case 9` ("My prints
don't stay attached to the plate."). The FakeEmbedder counts words, and
the manual says "build sheet" and "first layer does not stick", not "plate".
The right chunk `p3-bed-1` is still first, but with a score of 0.079, tied
with an unrelated conveyor chunk. The generator then replied that the
manuals have no information. Retrieval succeeded, generation failed. EXE01
and EXE02 show why a word count misses meaning.
