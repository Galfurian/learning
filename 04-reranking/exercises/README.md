# Exercises

Each exercise is one folder with three files:

```text
exeNN-topic/
├── README.md   # the task, the concept, and the runs with what to look at
├── exeNN.py    # the file you edit: one piece of the reranking stage, with a TODO
└── check.py    # verifies your file with fake data, without any model
```

Start with `exe00-demo`: it is solved. Then do the others in order. Each
builds one piece by hand; later exercises use the library version in
`src/reranklab/`, so a mistake in one does not break the next.
`exe08-benchmark` is solved again: the three pipelines on the holdout.

| #  | Folder                                              | You write                              | Concept |
|----|-----------------------------------------------------|----------------------------------------|---------|
| 00 | [exe00-demo](exe00-demo/)                           | nothing                                | first stage → reranker → generator; why `nomic-embed-text`; four actors |
| 01 | [exe01-two-stages](exe01-two-stages/)               | `rerank(question, hits, score, k)`     | two stages; the reranker reorders and cuts, never finds anything new |
| 02 | [exe02-ndcg](exe02-ndcg/)                           | `gain`, `ndcg_at_k`                    | section recall, evidence recall and nDCG measure different things |
| 03 | [exe03-cross-encoder](exe03-cross-encoder/)         | `score_pair(tokenizer, session, q, p)` | bi-encoder vs cross-encoder; a relevance score is not a probability |
| 04 | [exe04-decision-reranker](exe04-decision-reranker/) | `state_a`, `QUESTION_A`, `state_b`, `questions_b` | tev1 as a reranker; mode A vs mode B; position bias |
| 05 | [exe05-depth](exe05-depth/)                         | `depth_curve(...)`                     | the depth ceiling; what changes at equal recall |
| 06 | [exe06-cost](exe06-cost/)                           | `pick_config(rows, budget_s)`          | cost vs quality; the best configuration under a CPU budget |
| 07 | [exe07-diagnosis](exe07-diagnosis/)                 | `diagnose(row)`                        | the first failing stage: CANDIDATES → RERANK → GENERATION → NONE |
| 08 | [exe08-benchmark](exe08-benchmark/)                 | nothing                                | three pipelines on the holdout |

## Commands

Run from the unit folder (`04-reranking/`):

```bash
uv run python exercises/exe01-two-stages/check.py                 # verify, no model
uv run python exercises/exe01-two-stages/exe01.py --inspect       # setup, no model
uv run python exercises/exe01-two-stages/exe01.py --case 4        # one dev question
uv run python exercises/exe01-two-stages/exe01.py --question "…"  # a question of your own
uv run python exercises/exe01-two-stages/exe01.py --eval          # the dev-set metrics
```

Options shared by the exercises:

```bash
--first-stage nomic|gemma|bm25|fake      # the cheap retriever (default nomic)
--depth 20                               # N, candidates from the first stage
--top-k 3                                # k, chunks kept after reranking
--reranker none|minilm|bge|tev1-a|tev1-b|fake
--verbose                                # every HTTP request, labeled by actor
```

EXE00 and EXE08 also accept `--model`, `--think` and `--show-raw` for the
generator.

`OLLAMA_HOST=host:port` sends every Ollama request to another machine (see
the unit README). Keep one local model loaded at a time: `ollama stop
<model>` before you switch.

## Solutions

Reference solutions are in [solutions/](solutions/). Try first. To check a
solution, pass its path to the check:

```bash
uv run python exercises/exe05-depth/check.py exercises/solutions/exe05.py
```

## Extra

No scaffold. Measure on the dev set; report on the holdout only once.

1. **bge against MiniLM.** `--reranker bge` in EXE01–EXE05. Where does the
   larger model win, and what does it cost (EXE06)?
2. **tev1:0.8b against tev1:4b.** EXE04 with `--model-decision tev1:0.8b`.
   Quality per request, and the CPU time per question.
3. **Abstain on the reranker score.** Does a threshold on the MiniLM logit of
   the top candidate separate the 4 dev no-answer questions better than the
   cosine of unit 03 EXE05? Look at the count table of EXE03 first.
4. **Fused candidates.** Rerank the union of the BM25 and the `nomic` top 10.
   Does the depth ceiling rise without a larger N per retriever?
