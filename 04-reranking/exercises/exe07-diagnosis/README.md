# EXE07 — Which stage failed first?

**Concept:** a wrong answer does not say where the pipeline broke. A
recorded row does: it holds the N candidates of the first stage, the top k
after reranking, the answer and the code checks. The rule extends unit 03
EXE08 with the reranking stage.

```text
answerable question:
  1. no evidence chunk (gain 2) among the N candidates     -> CANDIDATES
  2. evidence among the candidates, none in the top k      -> RERANK
  3. evidence in the top k, facts or citations fail        -> GENERATION
  4. otherwise                                             -> NONE
no-answer question:
  refused -> NONE; any other answer -> GENERATION
```

The order matters: the first stage that failed wins, even if a later one
also failed.

## Operational, not causal

The rule names the first stage where the evidence is missing. It does not
prove that this stage is "wrong". A RERANK label can also come from:

- the gain definition (the facts were split over two chunks, so no chunk has
  gain 2);
- ties in the relevance scores;
- truncation of a long passage at `max_length`;
- the choice of k: a smaller k cuts more;
- noise of the reranker on near-identical passages.

The recorded rows show two of these effects:

- **k changes the label.** s05 ("What is PN-X2R-919-A?"): the evidence is
  the 15th candidate, and MiniLM puts it at rank 2. With k = 1 (r05) the
  label is RERANK; with k = 3 (r06) the evidence reaches the generator, and
  the label moves on to GENERATION. Same reranker, same scores.
- **N changes the label.** s02: with N = 5 (r01) the evidence is not among
  the candidates (CANDIDATES); with N = 20 (r02) it is the 20th candidate,
  MiniLM puts it first, and the answer is correct (NONE).

## Coarse labels

Facts and citations are code checks (unit 03 EXE06). r07 (s03, "The Ibis
R-26 shows E-6230. What should I check?") answered "Check the supply hose
and the inline filter", which is right, but did not say "3.0 bar", the
expected fact, so the label is GENERATION. r08 (s33) gave the right breaker,
CB-57, and cited `[lockout-breaker-57]`, an id that does not exist: the
facts check passes, the citation check fails.

## Task

1. Open `rows/r04-s28-default.json` and find, by hand: the first rank of the
   evidence among the candidates, and the gains of the top 3.
2. Implement `diagnose(row)` in `exe07.py`.

```bash
uv run python exercises/exe07-diagnosis/check.py
uv run python exercises/exe07-diagnosis/exe07.py
```

The check runs 8 synthetic cases, then the 10 recorded rows.

## The recorded rows

The rows come from real runs on the dev set (`scripts/record_rows.py`),
`nomic-embed-text` + MiniLM + `qwen3:1.7b`, with N = 5 or 20 and k = 1 or 3.

| row | stage      | what happened |
|-----|------------|---------------|
| r01 | CANDIDATES | s02 with N = 5: the evidence is the 20th candidate, out of reach |
| r02 | NONE       | s02 with N = 20: evidence moved from 20 to 1, correct answer |
| r03 | CANDIDATES | s07: the evidence is not among the 20 candidates |
| r04 | RERANK     | s28 (a paraphrase): evidence at ranks 5 and 8, the top 3 has none |
| r05 | RERANK     | s05 with k = 1: evidence at 15, reranked to 2, cut |
| r06 | GENERATION | s05 with k = 3: the evidence reaches the generator, the answer does not give the part |
| r07 | GENERATION | s03: right advice, but not the expected "3.0 bar" (coarse check) |
| r08 | GENERATION | s33: right fact, invented citation id |
| r09 | NONE       | s01: evidence at rank 1, correct and cited |
| r10 | NONE       | s34 (no answer exists): refused |

Over the whole dev set with the default settings (N = 20, k = 3), the
recordings gave 30 NONE, 5 GENERATION, 1 RERANK and 1 CANDIDATES: after
reranking, most remaining failures are in the generation.
