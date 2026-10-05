# Exercises

Each exercise is one folder with three files:

```text
exeNN-topic/
├── README.md   # the task, and what concept it teaches
├── exeNN.py    # the file you edit: one piece of the pipeline, with a TODO
└── check.py    # verifies your file with fake data, without any model
```

Start with `exe00-demo`: it is already solved, so you can read a working
pipeline and try every command before writing your own. Then do the others
in order. Each one builds one piece by hand. Later exercises use the library
version of that piece in `src/raglab/`, so a mistake in one exercise does not
break the next. `exe09-demo` is a solved demo again: a larger plant, three
ways to answer, and the holdout set.

| #  | Folder                                       | You write                                  | Concept |
|----|----------------------------------------------|--------------------------------------------|---------|
| 00 | [exe00-demo](exe00-demo/)                    | nothing                                    | the whole pipeline, solved; `--verbose` shows the three actors |
| 01 | [exe01-embeddings](exe01-embeddings/)        | `normalize`, two sentence pairs            | text becomes a fixed-size vector; Ollama vectors already have norm 1; fake vs real; closeness is not meaning |
| 02 | [exe02-similarity](exe02-similarity/)        | `cosine`, `top_k`                          | ranking by cosine; lexical vs semantic; a score is not a probability |
| 03 | [exe03-chunking](exe03-chunking/)            | `chunk_section(section, size, overlap)`    | size, overlap, the title line; R@k by section vs E@k by evidence |
| 04 | [exe04-retrieval](exe04-retrieval/)          | `search`, `recall_at_k`                    | the index and its cache; the dev set; recall by category |
| 05 | [exe05-context](exe05-context/)              | `build_context`, `answerable`, `THRESHOLD` | budget, order, ids; the score overlap; a threshold is a policy with a cost |
| 06 | [exe06-generation](exe06-generation/)        | the prompt, `check_citations`              | grounded answers; citations checked by code; a citation is not support |
| 07 | [exe07-hybrid](exe07-hybrid/)                | `keyword_search`, `fuse`                   | exact identifiers; two retrievers; reciprocal rank fusion |
| 08 | [exe08-diagnosis](exe08-diagnosis/)          | `diagnose(trace)`                          | the first point of failure: retrieval, context, generation, or none |
| 09 | [exe09-demo](exe09-demo/)                    | nothing                                    | manuals larger than the context; stuff vs pipeline vs MCP tool; holdout |

## Commands

Run from the unit folder (`03-rag/`):

```bash
uv run python exercises/exe04-retrieval/check.py                  # verify, no model
uv run python exercises/exe04-retrieval/exe04.py --inspect        # chunks and requests, no model
uv run python exercises/exe04-retrieval/exe04.py                  # run on every dev question
uv run python exercises/exe04-retrieval/exe04.py --eval           # the metric table
uv run python exercises/exe04-retrieval/exe04.py --case 8         # only question 8
uv run python exercises/exe04-retrieval/exe04.py --question "..." # a question of your own
uv run python exercises/exe04-retrieval/exe04.py --verbose        # every HTTP request and response
uv run python exercises/exe04-retrieval/exe04.py --fake-embed     # the bag-of-words baseline
uv run python exercises/exe04-retrieval/exe04.py --no-prefix      # without the documented prefixes
uv run python exercises/exe04-retrieval/exe04.py --embed-model nomic-embed-text
uv run python exercises/exe04-retrieval/exe04.py --top-k 5 --size 120 --overlap 20
```

Exercises that call the generator (00, 05, 06, 09) also accept:

```bash
--model qwen3:4b       # another generative model
--show-raw             # the exact rendered prompt
--think                # let the generator reason first
--budget 1500          # context budget, estimated tokens
--min-score 0.33       # drop hits below this score
--retriever hybrid     # semantic, keyword or hybrid
--record DIR           # one JSON trace per question (EXE08)
```

Keep one comparison model loaded at a time: `ollama stop <model>` before you
switch.

## Solutions

Reference solutions are in [solutions/](solutions/). Try first. To check a
solution, pass its path to the check:

```bash
uv run python exercises/exe04-retrieval/check.py exercises/solutions/exe04.py
```

## Extra

When the exercises are clear, try these on your own. There is no scaffold.

1. **Rerank with a decision model.** Retrieve the top 10, then ask `tev1`
   (unit 02) one `noul` question per hit: "Does this passage answer the
   question?". Reorder by its probability. Does R@1 improve on the dev set?
2. **Check support.** For each cited chunk, ask `tev1` "Does this passage
   state that <claim>?". Run it on `exe06-generation/recorded.json`: does it
   catch the wrong citation?
3. **The margin.** Abstain when the top-1 score minus the top-2 score is
   small, not only when the top-1 score is low. Does it separate the dev
   no-answer questions better than the EXE05 threshold?
4. **Route identifiers.** When the question contains a token that looks like
   a code or part number and appears in the corpus, use the keyword ranking
   first. Does it fix the d16 miss of `nomic-embed-text` in EXE07?
5. **Query rewriting.** Let the generator rewrite the question before
   retrieval. Measure R@3 before and after on the dev set.
6. **Compare embedding models on the holdout.** Run EXE09 `--mode pipeline` with
   `nomic-embed-text` and `qwen3-embedding:0.6b`, one at a time. Report it as
   a final result: do not go back and change `config.py`.
