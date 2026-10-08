# EXE04 — The decision model as a reranker

**Concept:** `tev1`, the decision model of unit 02, can be a reranker. Ask it
a `noul` question about each candidate — "Does the passage contain the answer
to the question?" — and sort the candidates by the probability it returns.

There are two ways to ask, and they are **two different methods**, not one
method and its cheaper version:

```text
mode A   one request per passage
         state = question + ONE passage, one noul question
         -> independent judgments: no passage can influence another

mode B   one request for all the passages
         state = question + ALL N passages, N noul questions (p1 ... pN)
         -> every judgment sees the other passages,
            and the ORDER of the passages in the state can change the answers
```

Mode B needs 1 request per question instead of N, but it changes the
problem. Unit 02 EXE06 showed the same effect: questions asked together can
influence each other. Here the candidates do.

The `noul` value is the probability of the model's answer to *its* question,
not a probability that the passage is relevant; and its scale is not the
cross-encoder's scale.

## Local or remote Ollama

`OLLAMA_HOST` chooses the server, as for the `ollama` CLI. Unset, the unit
uses the local machine. With `export OLLAMA_HOST=<host>:11434` it uses a lab
machine with a GPU. The header line says where the times come from. **GPU
times are not CPU costs**: EXE06 measures the CPU cost of tev1 on the local
machine.

## Task

Implement `state_a`, `QUESTION_A`, `state_b` and `questions_b` in `exe04.py`.

```bash
uv run python exercises/exe04-decision-reranker/check.py
uv run python exercises/exe04-decision-reranker/exe04.py --inspect
```

`--inspect` prints one state of each mode and calls no model.

## Run, one step at a time

On a CPU-only machine tev1 takes seconds per request: run step 1 locally,
and steps 2–3 on a faster machine through `OLLAMA_HOST` if you have one. The
first run fills the score cache; a second run says `cached` and costs
nothing.

### 1. One question, three ways

```bash
uv run python exercises/exe04-decision-reranker/exe04.py --case 16 --depth 10 --modes A,B,B-reversed
```

"The Heron M-58 stopped and the screen shows no code. Why?" Compare the
score of the same chunk in the three tables.

Measured (lab GPU): all three put `mill4-troubleshooting-1` (the evidence,
first-stage rank 9) at rank 1. Its score was 0.867 in mode A, 0.366 in mode
B, and 0.994 in mode B with the passages reversed. Same question, same
passage, same model: only the other passages and their order changed.

### 2. The dev set, every mode

```bash
uv run python exercises/exe04-decision-reranker/exe04.py --eval --depth 10
```

Measured (`nomic-embed-text`, N = 10, `tev1:4b-q4_K_M`, lab GPU):

|                | `evidence_recall@1` | `evidence_recall@3` | MRR   | `nDCG@3` | requests | s/question (GPU) |
|----------------|---------------------|---------------------|-------|----------|----------|------------------|
| first stage    | 0.636               | 0.727               | 0.709 | 0.661    | 0        | –                |
| tev1 A         | 0.879               | 0.909               | 0.894 | 0.818    | 370      | 1.1              |
| tev1 B         | 0.879               | 0.909               | 0.889 | 0.843    | 37       | 1.1              |
| tev1 B-reversed| 0.818               | 0.848               | 0.847 | 0.799    | 37       | 1.0              |
| tev1 B-shuffled| 0.848               | 0.909               | 0.869 | 0.823    | 37       | 1.1              |

### 3. Position bias

Look at the three B rows: same candidates, same model, only the order in the
prompt differs, and `evidence_recall@1` moves from 0.879 to 0.818. In mode B
the position of a passage is part of the input. Mode A has no such effect:
each passage is judged alone.

On the lab GPU, A and B cost about the same time (1.1 s per question)
although A sends 10 times more requests. On a CPU it is different: EXE06
measures it.
