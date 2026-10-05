# 03 — RAG with local models

Goal: understand retrieval-augmented generation by building every piece of
it: embeddings, similarity, chunking, retrieval, the context, generation,
hybrid search and diagnosis. For each piece, see how it fails and measure
it.

The example deliberately avoids frameworks and vector databases. The whole
API is two HTTP requests, `POST /api/embed` and `POST /api/chat`. The
interesting part is the code around them.

## What you will build

```text
data/dev/manuals/*.md               invented manuals
    |
    | chunk_section()               <-- APP code (EXE03; src/raglab/chunking.py)
    v
chunks ──> POST /api/embed           <-- EMBEDDING MODEL: text -> vector (embeddinggemma)
    |
    v
index: one matrix of unit vectors   <-- APP code (EXE04; src/raglab/index.py), cached on disk
    ^
    | question -> POST /api/embed -> top k chunks       (EXE02, EXE04, EXE07)
    |
context: chunks with [ids]          <-- APP code (EXE05; src/raglab/context.py)
    |
    | POST /api/chat                 <-- GENERATIVE MODEL: question + context -> answer (qwen3:1.7b)
    v
answer with citations ──> checks    <-- APP code (EXE06; src/raglab/generation.py)
```

The embedding model never sees the question and the manuals together. The
generative model never sees the manuals: it reads only what the APP puts in
the context. In EXE09 the generator can also call an MCP tool to search by
itself, which adds a fourth actor, the MCP server.

All documents are invented. If the generator already knew the answers, a
correct answer would prove nothing about retrieval.

## Prerequisites

Inside WSL:

- Python 3.11+
- `uv`
- Ollama 0.35 or later at `http://localhost:11434`
- `embeddinggemma` (621 MB) and `qwen3:1.7b` (1.4 GB)
- optional, for comparisons: `nomic-embed-text` (274 MB), `qwen3:4b`
  (2.5 GB), `qwen3-embedding:0.6b` (639 MB)

## 0. Clone the learning repo

```bash
git clone git@github.com:Galfurian/learning.git
cd learning/03-rag
```

## 1. Install the Python workspace

```bash
uv sync
```

If you do not have uv yet, see [unit 01](../01-mcp-local-llm/README.md#1-install-the-python-workspace).

## 2. Prepare Ollama

The complete WSL/Linux setup lives in [../docs/ollama.md](../docs/ollama.md).
For this unit:

```bash
ollama pull embeddinggemma
ollama pull qwen3:1.7b
ollama pull nomic-embed-text      # optional
curl http://localhost:11434/api/embed -d '{"model": "embeddinggemma", "input": ["hello"]}'
```

The `curl` line returns one vector of 768 numbers. An embedding model is not
a chat model: `ollama run embeddinggemma` is not the way to use it.

The two default models are small enough to stay loaded together. Keep only
one comparison model loaded at a time: `ollama stop <model>` before you
switch.

## 3. First without a model

```bash
uv run python exercises/exe00-demo/check.py
uv run python exercises/exe00-demo/exe00.py --inspect
```

The check tests the APP code with fake hits. `--inspect` shows the chunks
and the system prompt, without calling any model.

## 4. Let the models answer

```bash
uv run python exercises/exe00-demo/exe00.py --case 3
```

The first run embeds the 43 chunks (about 6 s on CPU) and caches them in
`.cache/embeddings/`. For each question you see the retrieved chunks with
their scores, the context, and the answer:

```text
│ 1 │ lx40-cooling-1         │ 0.657 (cosine) │ ✓ │
│ 2 │ lx40-troubleshooting-2 │ 0.554 (cosine) │   │
│ 3 │ lx40-errors-2          │ 0.502 (cosine) │   │
...
╭──────────────── Answer · GENERATIVE MODEL ────────────────╮
│ The coolant should be between 15 and 22 °C. [lx40-cooling-1] │
╰── qwen3:1.7b · 6.5s · prompt 358 tokens (estimated context 214) · citations ok ──╯
```

## 5. See the inner workings

```bash
uv run python exercises/exe00-demo/exe00.py --verbose --case 3
uv run python exercises/exe00-demo/exe00.py --show-raw --case 3
```

`--verbose` shows every HTTP request and response, labeled by actor:
`APP -> EMBEDDING MODEL` (the question, and 768 floats back, shortened on
screen) and `APP -> GENERATIVE MODEL` (the messages, and the answer back).

`--show-raw` shows the exact text the generator reads, after Ollama applies
its chat template. It uses `_debug_render_only`, an undocumented Ollama
debug field (tested on Ollama 0.35.0); if a later version drops it, the
flag reports an error.

### All options

| Option              | Effect |
|---------------------|--------|
| `--inspect`         | show chunks and requests without calling any model |
| `--verbose`         | show every HTTP request and response, labeled by actor |
| `--question "..."`  | ask this question instead of the eval set |
| `--case N`          | run only question N of the eval set |
| `--eval`            | run the whole eval set and print the metric table |
| `--top-k K`         | number of chunks to retrieve |
| `--size N`, `--overlap N` | chunk size and overlap, in words |
| `--embed-model M`   | another embedding model |
| `--fake-embed`      | the FakeEmbedder: hashed word counts, no model |
| `--no-prefix`       | embed without the model's documented prefixes |
| `--model M`         | another generative model |
| `--budget N`        | context budget, estimated tokens |
| `--min-score S`     | drop hits below this score before building the context |
| `--retriever R`     | `semantic`, `keyword` or `hybrid` |
| `--show-raw`        | the exact rendered prompt |
| `--think`           | let the generator reason first |
| `--record DIR`      | write one JSON trace per question |

## 6. Read the code in this order

1. `exercises/exe00-demo/exe00.py` and `check.py`.
2. `docs/mental-model.md`: the actors, vectors, cosine, chunking, metrics,
   the threshold, citations, hybrid search, diagnosis, dev vs holdout.
3. `src/raglab/client.py`: the two HTTP requests.
4. `src/raglab/embedders.py`: the real embedder (prefixes, cache) and the
   FakeEmbedder.
5. `src/raglab/index.py`: the matrix and the search.
6. `src/raglab/context.py`, `generation.py`, `pipeline.py`: the context, the
   prompt and the citation check, one question end to end.
7. `src/raglab/runners.py`: the run loop of each exercise.
8. `src/raglab/ui.py`: Rich rendering; useful for learning, not part of the
   logic.

## 7. Write your own pieces

Continue with [exercises/README.md](exercises/README.md): eight exercises,
each a file with a TODO and a check, then a final demo on a plant whose
manuals do not fit in the generator's context.

## Files

```text
03-rag/
├── README.md
├── pyproject.toml
├── data/
│   ├── dev/                 # 4 manuals + 26 dev questions (EXE01–EXE08)
│   └── plant/               # 40 generated manuals + 20 holdout questions (EXE09)
├── docs/
│   └── mental-model.md
├── scripts/
│   └── measure_dev.py       # retrieval metrics for one embedder
├── src/
│   └── raglab/              # plumbing shared by all exercises
│       ├── client.py        # POST /api/embed, POST /api/chat
│       ├── embedders.py     # OllamaEmbedder, FakeEmbedder
│       ├── cache.py         # embedding cache on disk
│       ├── corpus.py        # manuals -> sections
│       ├── chunking.py      # sections -> chunks
│       ├── index.py         # vectors + search
│       ├── evalset.py       # questions, R@k, E@k, MRR
│       ├── context.py       # hits -> context
│       ├── generation.py    # prompt, citation check
│       ├── pipeline.py      # one question end to end, traces
│       ├── hybrid.py        # BM25, reciprocal rank fusion
│       ├── agent.py         # EXE09 tool mode: MCP client + tool loop
│       ├── exercise.py      # shared command line
│       ├── runners.py       # the run loop of each exercise
│       ├── checks.py        # checker and fakes
│       └── ui.py            # Rich rendering
├── tests/                   # tests of src/raglab
└── exercises/
    ├── README.md
    ├── exe00-demo/ … exe09-demo/
    └── solutions/
```

## The key lesson

Three parts do three jobs. The embedding model turns text into vectors and
knows nothing about your question. Your code decides what is a chunk, what
is retrieved, what the generator reads, when to abstain, and checks the
answer. The generator writes the answer from what it is given. Measure each
part on its own, on a dev set, and verify the whole once on questions you
did not tune on.
