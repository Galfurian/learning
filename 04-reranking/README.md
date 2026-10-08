# 04 — Reranking

Goal: put a second, more expensive judgment between retrieval and generation,
and measure what it buys. A cheap first stage finds candidates; a reranker
reads the question and each candidate together and reorders them; the
generator reads the top few.

The central rule of this unit: **a reranker can only reorder the candidates
the retriever already found.**

No frameworks, no vector database. The rerankers are visible: a cross-encoder
run with ONNX Runtime (tokens in, one logit out) and the decision model of
unit 02 asked one question per candidate.

## What you will build

```text
data/plant/manuals/*.md          the plant of unit 03: 40 machines, 600 chunks
    |
    | FIRST STAGE                <-- retriever.py: nomic-embed-text, embeddinggemma, BM25, FakeEmbedder
    v
N candidates (default 20)
    |
    | RERANKER                   <-- rerankers.py: MiniLM cross-encoder (ONNX) or tev1 (Ollama)
    v
top k (default 3)
    |
    | GENERATOR                  <-- qwen3:1.7b, prompt and citation check from unit 03
    v
answer, scored by metrics.py; first failing stage by benchmark.py; cost by costs.py
```

The first stage scores chunks alone (fast, cacheable). The reranker scores
pairs (slow): that is why it sees only N candidates, and why N matters.

## Prerequisites

Inside WSL:

- Python 3.11+ and `uv`
- Ollama 0.35 or later
- `nomic-embed-text`, `embeddinggemma`, `qwen3:1.7b`, `tev1:4b-q4_K_M`
- the ONNX cross-encoders download from Hugging Face on first use (about
  90 MB for MiniLM, 280 MB for bge), at the pinned revisions in
  `src/reranklab/rerankers.py`

## 0. Clone and install

```bash
git clone git@github.com:Galfurian/learning.git
cd learning/04-reranking
uv sync
```

## 1. Prepare Ollama

See [../docs/ollama.md](../docs/ollama.md). For this unit:

```bash
ollama pull nomic-embed-text
ollama pull embeddinggemma
ollama pull qwen3:1.7b
ollama pull tev1:4b-q4_K_M
```

Keep one model loaded at a time on a laptop: `ollama stop <model>` before you
switch.

## 2. Local or remote Ollama

Every Ollama call goes to `OLLAMA_HOST`, with the same meaning as for the
`ollama` CLI. Unset, it is the local machine:

```bash
uv run python exercises/exe00-demo/exe00.py --case 2    # local

export OLLAMA_HOST=<host>:11434                          # another machine, for this shell
ollama pull tev1:4b-q4_K_M                               # pulls there
uv run python exercises/exe00-demo/exe00.py --case 2    # runs there
unset OLLAMA_HOST                                        # back to the local machine
```

The unit is designed for a CPU-only machine. tev1 takes about 5 s per
candidate on a CPU (EXE06), so a GPU machine makes EXE04 and EXE08 practical.
**GPU times are not CPU costs**: every table says where its times come from.

## 3. First without a model

```bash
uv run python exercises/exe00-demo/check.py
uv run python exercises/exe00-demo/exe00.py --inspect
```

## 4. Let the models run

```bash
uv run python exercises/exe00-demo/exe00.py --case 2
```

"On the Tamarin C-83, what is E-5310?" The first-stage table shows 20
candidates with their gains; the evidence chunk is the 20th. The reranked
table shows it moved:

```text
                           Reranked by minilm · top 3
┏━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┓
┃ rank   ┃ from     ┃ chunk                      ┃ relevance score     ┃ gain  ┃
┡━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━┩
│ 1      │ 20 → 1   │ conveyor4-errors-2         │ 7.047               │ 2     │
│ 2      │ 1 → 2    │ conveyor4-errors-1         │ 5.547               │ 1     │
│ 3      │ 2 → 3    │ conveyor4-overview-1       │ 4.000               │ 0     │
└────────┴──────────┴────────────────────────────┴─────────────────────┴───────┘
answer: E-5310: sensor S42 does not respond. Check its cable at terminal X19.
```

`--verbose` shows the requests of the EMBEDDING MODEL and the GENERATIVE
MODEL. MiniLM runs inside the Python process: it has no HTTP request.

### All options

| Option                  | Effect |
|-------------------------|--------|
| `--inspect`             | show the setup without calling a model |
| `--verbose`             | show every HTTP request and response, labeled by actor |
| `--question "..."`      | ask this question instead of the dev set |
| `--case N`              | run only question N of the dev set |
| `--eval`                | run the whole set and print the metrics |
| `--first-stage S`       | `nomic` (default), `gemma`, `bm25`, `fake` |
| `--depth N`             | candidates from the first stage (default 20) |
| `--top-k K`             | chunks kept after reranking (default 3) |
| `--reranker R`          | `none`, `minilm` (default), `bge`, `tev1-a`, `tev1-b`, `fake` |
| `--model M`             | generator (EXE00, EXE08) |
| `--think`, `--show-raw` | generator reasoning, rendered prompt (EXE00, EXE08) |

## 5. Read the code in this order

1. `exercises/exe00-demo/exe00.py` and `check.py`.
2. `docs/mental-model.md`.
3. `src/reranklab/retriever.py`: the first stages.
4. `src/reranklab/rerankers.py`: `rerank()`, the cross-encoder, tev1 modes A
   and B, the fake reranker.
5. `src/reranklab/metrics.py`: gains, recalls, MRR, nDCG, abstention.
6. `src/reranklab/costs.py`: timings and the budget choice.
7. `src/reranklab/benchmark.py`: one question end to end, the first failing
   stage.
8. `src/reranklab/runners.py`: the run loop of each exercise.

The other modules (`client`, `embedders`, `index`, `bm25`, `generation`, …)
are copies from unit 03, trimmed; each says so in its first line.

## 6. Write your own pieces

Continue with [exercises/README.md](exercises/README.md): seven exercises
with a TODO and a check, then the benchmark on the holdout.

## Files

```text
04-reranking/
├── README.md
├── pyproject.toml
├── data/
│   ├── plant/              # the unit 03 manuals and their generator
│   ├── dev.json            # 37 dev questions
│   └── holdout.json        # 20 holdout questions
├── docs/mental-model.md
├── scripts/
│   ├── measure_tev1_cpu.py # the CPU cost of tev1, local only
│   └── record_rows.py      # rows for EXE07
├── src/reranklab/          # new: retriever, rerankers, scorecache, metrics, costs, benchmark
├── tests/
└── exercises/
```

## The key lesson

A reranker can only reorder the candidates the retriever already found.
Choose the first stage for its recall at N, the reranker for the order of
those N, and N for the cost you can pay. Measure each on the dev set, and
verify the whole once on questions you did not tune on.
