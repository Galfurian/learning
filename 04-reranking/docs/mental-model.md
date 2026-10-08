# Mental model: reranking

Numbers come from runs on the dev set (37 questions, 33 with an answer) and
the holdout (20 questions), on the plant manuals of unit 03 (600 chunks).

## 1. Two stages

```text
QUESTION
   ├── FIRST STAGE   cheap: scores every chunk alone              -> N candidates
   ├── RERANKER      expensive: reads question + passage together -> new order, top k
   └── GENERATOR     reads the top k                              -> answer
```

The first stage can look at all 600 chunks because each chunk's vector is
computed once, without the question. The reranker reads the question and a
passage together, so it must run once per pair: 600 pairs per question would
be too slow, N = 20 is affordable.

**A reranker can only reorder the candidates the retriever already found.**

## 2. Bi-encoder and cross-encoder

- **Bi-encoder** (the first stage, unit 03): `cosine(embed(q), embed(d))`.
  Fast, cacheable, blind to how the two texts relate.
- **Cross-encoder** (MiniLM): `(q, d) -> one forward pass -> one logit`. The
  model reads `[CLS] question [SEP] passage [SEP]`, so it can match the
  question's code or machine name against the passage's.

For "What does E-4210 mean on the Kestrel LX-69?", the first stage's cosines
of the top candidates were all between 0.68 and 0.72, with the evidence at
rank 6. MiniLM's logits spread from 6.59 (the evidence) to 2.43.

## 3. The decision model as a reranker

`tev1` answers a `noul` question per candidate: "Does the passage contain the
answer to the question?"

- **Mode A**, one request per passage: independent judgments.
- **Mode B**, one request for N passages: every judgment shares the state with
  the other passages. A different method, not a cheaper mode A. The order of
  the passages changes the result: `evidence_recall@1` 0.879 with the
  original order, 0.818 reversed. One passage scored 0.867 in mode A, 0.366 in
  mode B, 0.994 in mode B reversed.

## 4. Relevance scores are not probabilities

The cross-encoder returns a logit (about -11 to +10 here); its sigmoid is in
(0, 1) but not calibrated: seven chunks of one question had sigmoids between
0.97 and 0.999, and one was relevant. tev1's `noul` value is the probability
of its own answer, on another scale. Across questions, the logits of evidence
chunks and irrelevant chunks overlap (66 irrelevant chunks between 5.8 and
7.9). Scores order the candidates of one question; a fixed threshold on them
is a policy, as in unit 03 EXE05.

## 5. Three questions, three metrics

| Metric              | Question |
|---------------------|----------|
| `section_recall@k`  | right section in the top k? |
| `evidence_recall@k` | a chunk with every expected fact (gain 2) in the top k? |
| `nDCG@k`            | how well ordered is the top k, with gains 2 / 1 / 0? |

MRR uses the first evidence chunk. A reorder can change nDCG at equal
recall, in both directions: on the dev set two questions improved and two got
worse at the same `evidence_recall@3`.

## 6. The depth ceiling

For presence metrics, `evidence_recall@1` after reranking ≤
`evidence_recall@N` of the first stage. With the FakeEmbedder the reranker
reached the ceiling exactly up to N = 20 (0.697, 0.848, 0.970). With `nomic`
the ceiling was 1.000 at N = 50 and the reranked value 0.939. With
`embeddinggemma` a larger N made things worse (0.970 → 0.939 at N = 50): more
candidates, more distractors.

## 7. Cost

Measured on a CPU-only laptop: MiniLM 10–24 ms per pair; tev1 4.9 s per pair
in mode A (49 s per question at N = 10), 38 s per question in mode B. On the
dev set, BM25 + MiniLM at N = 20 was the best configuration under any budget
from 0.5 s to 60 s per question. GPU times from a lab machine (about 1 s per
question for tev1) are not CPU costs.

## 8. The no-answer side

A reranker always returns a top k, relevant or not: for a question with no
answer, every candidate has gain 0 and the reranker still orders them. The
refusal comes from the generator. On the holdout every pipeline refused the 3
no-answer questions (`false_answer_rate` 0.00).

## 9. The first failing stage

```text
CANDIDATES -> RERANK -> GENERATION -> NONE
```

An operational label, not a causal proof: the same question was RERANK with
k = 1 and GENERATION with k = 3, and CANDIDATES with N = 5 and NONE with
N = 20. With N = 20 and k = 3 on the dev set, most remaining failures were in
the generation (5 GENERATION, 1 RERANK, 1 CANDIDATES out of 37).

## 10. Dev versus holdout

The dev set chose N, k, the reranker and the budget. The holdout (20 new
questions on 8 machines the dev set does not use) was committed before the
first benchmark run. On the holdout, both rerankers lifted the `nomic`
pipeline from 0.65 to 0.88–0.94 `evidence_recall@1`; with `embeddinggemma`
the retrieval improved and the answers did not, because near-identical parts
lists of sibling machines reached the generator together.

## 11. Local or remote Ollama

`OLLAMA_HOST` chooses the Ollama server, as for the `ollama` CLI. The unit is
designed for a CPU-only machine; a remote GPU machine makes the tev1
experiments practical, and its times are labeled as GPU times.
