# Mental model: retrieval-augmented generation

The numbers in this document come from runs on the dev set
(`data/dev/`, 4 invented manuals, 43 chunks, 26 questions), with
`embeddinggemma` and `qwen3:1.7b` unless stated otherwise.

## 1. The pipeline and its actors

```text
DOCUMENTS ── chunk ── embed ── store vectors                      (once, cached)

QUESTION ── embed ── nearest chunks ── build context ── LLM ── answer with citations
```

Three responsibilities:

```text
EMBEDDING MODEL    text -> vector                                   (Ollama /api/embed)
APP CODE           vectors -> relevant chunks -> context -> checks  (your code)
GENERATIVE MODEL   question + retrieved chunks -> answer            (Ollama /api/chat)
```

The embedding model reads one text at a time and returns numbers. The
generative model reads only what the APP puts in the context. Everything in
between is ordinary code: what a chunk is, how many chunks come back, what
the generator reads, when to abstain, how the answer is checked.

In EXE09 `--mode tool` a fourth actor runs: the **MCP SERVER**. The
generative model asks for the tool `search_manuals`, the APP (as MCP host)
sends `tools/call`, and the server runs the retrieval. Then the generator,
not the APP, decides when to search and with which query.

## 2. What a vector is

An embedding is a list of fixed size: 768 numbers for `embeddinggemma`,
whatever the length of the text. Its direction carries the meaning, as the
model learned it. Ollama `/api/embed` returns unit vectors (norm 1.0000), so
for two Ollama vectors the cosine is the dot product. Check what your
endpoint returns before you normalize: the FakeEmbedder of this unit returns
raw counts, and for those the APP must normalize.

## 3. Cosine and ranking

Retrieval is ranking: score every chunk against the question and keep the
best k. With unit vectors, one matrix-vector product scores all chunks.

**A similarity score is not a probability or a confidence.** A cosine of 0.6
does not mean "60% relevant". It is a geometric quantity, and its scale
depends on the model, the prefixes and the texts:

- with `embeddinggemma`, a correct top-1 can score 0.349, and the top-1 of a
  question the manuals cannot answer can score 0.558;
- with `nomic-embed-text`, the same no-answer questions score 0.626–0.724;
- "The nozzle is clogged" and "The nozzle is clean" score 0.852, higher than
  two sentences with the same meaning (0.633).

## 4. Chunking

The chunk is the unit of retrieval: one chunk, one vector. Small chunks lose
the words that give them meaning; large chunks average many topics. The
title line (`<manual> — <section>`) on every chunk tells the embedding which
machine a sentence is about: without it, E@1 drops from 0.955 to 0.864.

## 5. Measuring retrieval

Measure retrieval before you generate anything: if the right section is not
retrieved, no prompt fixes the answer.

- **R@k** (recall at k): the fraction of answerable questions with a chunk
  of a relevant section in the top k. Labels point at sections, so they do
  not change with the chunk size.
- **MRR**: the mean of 1 / rank of the first relevant chunk.
- **E@k** (evidence at k): the top k chunks contain the facts a correct
  answer needs. R@k can say "found" when the chunk found holds the wrong half
  of the section; E@k cannot.

Dev results at k = 3: `embeddinggemma` R@3 1.000; `nomic-embed-text` 0.909;
the FakeEmbedder (bag of words) 0.864.

## 6. The context and the threshold

The context is all the generator reads: chunks in rank order, each with its
`[id]`, within a token budget. The APP can also abstain and not call the
generator at all.

A threshold on the top-1 score is a **policy with a cost**, not a solution.
On the dev set, the top-1 scores of answerable and no-answer questions
overlap (0.349 vs 0.558): every threshold refuses some answerable questions
or passes some no-answer questions. Choose it from the cost of each error,
on the dev set, for one embedding model, and expect the generator's refusal
to be the second check.

## 7. Generation and citations

The prompt asks the generator to use only the excerpts, to cite their ids,
and to reply "Not in the manuals." otherwise. The APP checks the citations.

**A citation that exists is not a citation that supports the claim.** In a
real run, "PN-X7S-919-A is a convection fan motor. [p3-parts-1]" was right,
and cited the 3D printer's parts list, which does not contain that part
number. The citation check accepted it. Code can prove that the cited id is
in the context. It cannot prove that the cited text says what the answer
says.

## 8. Hybrid search

Semantic search matches meaning; keyword search matches exact tokens.
`PN-X7Q-919-A` and `PN-X7R-919-A` differ by one character, and that
character is the meaning. Keyword search found every dev part number with
either embedder; `nomic-embed-text` alone missed one completely.
Reciprocal rank fusion (RRF) mixes rankings, not scores, because the scores
are on different scales. On the dev set plain RRF did not rescue the missed
part number: it favors chunks that both retrievers rank high. On the EXE09
holdout, with 40 look-alike spare-parts lists, semantic retrieval missed both
questions that contain only a part number, and hybrid retrieval found them
(evidence 15/17 -> 17/17). The generator then read the wrong line of the
list: retrieval fixed, generation still failed.

## 9. Diagnosis

A wrong answer does not say where the pipeline broke. A trace does. The
first point of failure, in order:

```text
1. no hit from a relevant section                  -> RETRIEVAL
2. relevant hit, but not in the final context      -> CONTEXT
3. relevant chunk in context, answer wrong or
   not supported by the cited chunks               -> GENERATION
4. answer correct                                  -> NONE
```

For a question the manuals cannot answer, a refusal is NONE and any other
answer is GENERATION. On the dev set, every recorded GENERATION failure had
the right chunk in the context.

## 10. Dev versus holdout

EXE01–EXE08 choose the chunk size, k, a threshold, the retriever and the
prompt on the dev set. EXE09 checks the final system once, on 20 holdout
questions written before the first EXE09 run and not changed after it. If
you tune on the questions you report, the report measures your tuning. The
limit: the same author wrote the corpus and the questions, so the holdout is
a discipline, not a guarantee.

## 11. What a vector database adds

This unit keeps its vectors in one NumPy matrix and searches it with one
product. For a few hundred vectors that takes microseconds. A vector
database adds what larger systems need:

- approximate nearest-neighbour search, so millions of vectors are searched
  without scoring every one;
- metadata filters ("only manuals of cell 3");
- persistence, updates and deletes without rebuilding the matrix;
- concurrent access and scale across machines.

None of these changes the pipeline above. They change how step 3 is done at
scale.
