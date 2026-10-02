# 02 — Decision models with a local model

Goal: understand what a decision model is, what it can and cannot decide, and
how to use one inside an application: build the **state**, ask typed
**questions**, read the **probabilities**, and let ordinary code **act** on
them.

The example deliberately avoids SDKs and frameworks. The whole API is one HTTP
request, and the interesting part is what happens before and after it.

## What you will build

```text
application data (tickets, emails, records)
    |
    | build_state()                 <-- APP code, the part you write
    v
state + questions
    |
    | POST /v1/systemone            <-- src/declab/client.py, one HTTP request
    v
Ollama + decision model (tev1)      <-- returns probabilities, never acts
    |
    v
answers: choice / noul / score + probabilities
    |
    | act()                         <-- APP code, the part you write
    v
an action: a queue, a reply, a refund, a person to call
```

Each exercise file has some application data (`CASES`), the questions to ask
(`QUESTIONS`), and the application code around the model (`build_state()` and
`act()`). Running it sends one request per case and shows what the model
answered and what your code did with it.

The first exercise, `exe00-demo`, is already solved: it triages support
tickets into teams and flags refund requests.

## Prerequisites

Inside WSL:

- Python 3.11+
- `uv`
- Ollama **0.35 or later** reachable at `http://localhost:11434` (decision
  models need the `/v1/systemone` endpoint added in 0.35)
- a decision model: `tev1:4b-q4_K_M` (default, 2.7 GB) and optionally
  `tev1:0.8b` (0.8 GB) to compare

## 0. Clone the learning repo

```bash
git clone git@github.com:Galfurian/learning.git
cd learning/02-decision-models
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
ollama --version                 # must be 0.35 or later
curl http://localhost:11434/api/tags
ollama pull tev1:4b-q4_K_M
ollama pull tev1:0.8b            # optional, for comparisons
```

`ollama show tev1:4b-q4_K_M` lists `decision` among the capabilities. A
decision model is not a chat model: `ollama run tev1:4b-q4_K_M` is not the way
to use it.

Check the endpoint with one request:

```bash
curl http://localhost:11434/v1/systemone -d '{
  "model": "tev1:4b-q4_K_M",
  "state": "Our checkout has returned 500 errors since 9am.",
  "questions": {"outage": {"type": "noul", "instructions": "Is a service down or failing?"}}
}'
```

The first request loads the model (several seconds on CPU); the next ones are
faster.

On a laptop, keep **one** decision model in memory at a time. Before you
switch model, unload the other one:

```bash
ollama ps
ollama stop tev1:4b-q4_K_M
```

## 3. First understand the application without the model

Open [exercises/exe00-demo/exe00.py](exercises/exe00-demo/exe00.py). It has
three parts:

- `CASES`: three support tickets (application data);
- `QUESTIONS`: a `choice` question (`team`) and a `noul` question (`refund`);
- `act()`: ordinary Python that turns the answers into a queue name.

Look at the requests the application would send, without calling the model:

```bash
uv run python exercises/exe00-demo/exe00.py --inspect
```

Then verify the application code, still without the model:

```bash
uv run python exercises/exe00-demo/check.py
```

Read `check.py`: it builds **fake answers** with exactly the shape Ollama
returns, and checks what `act()` does with them. This step matters: the
behavior of your application lives in your code, so you can test it without
any model. The model only fills in the numbers.

The concepts are explained in [docs/mental-model.md](docs/mental-model.md).

## 4. Let the model decide

```bash
uv run python exercises/exe00-demo/exe00.py
```

For every case you see the state, what the model answered, and what the app
did:

```text
──────────────────────────────── CASE 1/3 ────────────────────────────────
╭───────────────────── State · what the model reads ─────────────────────╮
│ Hi, you charged my card twice for the October plan. Please refund one  │
│ of the payments.                                                       │
╰────────────────────────────────────────────────────────────────────────╯
╭──────────── Decision · the MODEL answered (tev1:4b-q4_K_M) ────────────╮
│ team  choice -> billing   confidence 0.982                             │
│     billing               ████████████████████████ 0.997               │
│     technical             ░░░░░░░░░░░░░░░░░░░░░░░░ 0.003               │
│     other                 ░░░░░░░░░░░░░░░░░░░░░░░░ 0.001               │
│     account               ░░░░░░░░░░░░░░░░░░░░░░░░ 0.000               │
│ refund  noul  P(true) ██████████████████████░░ 0.921                   │
│                                                                        │
│ 1 request(s) · 456 input tokens · 3 output tokens · 11.37s             │
╰────────────────────────────────────────────────────────────────────────╯
╭────────────────── Action · your APP code acted (act) ──────────────────╮
│ put in queue/billing, tagged 'refund-request'                          │
╰────────────────────────────────────────────────────────────────────────╯
```

The green panel is the model's only contribution: numbers. The magenta panel
is your code. A summary table at the end puts all the cases side by side.

Ask about a ticket of your own:

```bash
uv run python exercises/exe00-demo/exe00.py --state "I was billed 49 euros but my plan costs 39. Why?"
```

It goes to `billing`, but the `refund` probability is low (about 0.12): the
customer asks a question, not for money back.

### See the inner workings

```bash
uv run python exercises/exe00-demo/exe00.py --verbose
```

Verbose mode starts with the two actors:

- **APP**: the exercise file (here `exe00.py`). It builds the state, asks the
  questions, and runs `act()`. Only the APP does things.
- **OLLAMA**: the local runtime serving `/v1/systemone` with the decision
  model. It reads state + questions and returns probabilities. It never acts.

Then, for every request, it shows the exact JSON body the APP sends
(`APP -> OLLAMA`) and the exact JSON Ollama returns (`OLLAMA -> APP`). There is
nothing else: no conversation history, no tool calls, no second round.

### All options

Every exercise file accepts the same options:

| Option           | Effect                                                         |
|------------------|----------------------------------------------------------------|
| `--inspect`      | show the requests and validate them locally, without the model |
| `--verbose`      | show every HTTP request and response                           |
| `--case N`       | run only case N of `CASES`                                     |
| `--state "..."`  | send this state instead of the cases (JSON is parsed)          |
| `--separately`   | one request per question instead of one per case               |
| `--model NAME`   | use another decision model, for example `tev1:0.8b`            |

## 5. Read the code in this order

1. `exercises/exe00-demo/exe00.py`: cases, questions, and the code that acts.
2. `exercises/exe00-demo/check.py`: the application tested with fake answers.
3. `docs/mental-model.md`: state, question types, probabilities, confidence,
   and the line between deciding and acting.
4. `src/declab/client.py`: the whole API, one `POST`.
5. `src/declab/exercise.py::run`: build the state, ask, act, for every case.
6. `src/declab/questions.py`: the request rules, and the confidence formula.
7. `src/declab/checks.py`: how fake answers are built.
8. `src/declab/ui.py`: Rich rendering; useful for learning, not part of the
   logic.

## 6. Write your own decision code

Continue with [exercises/README.md](exercises/README.md): seven exercises,
each one a file with a TODO and a check, then a final demo on a simulated
production line.

## Files

```text
02-decision-models/
├── README.md
├── pyproject.toml
├── src/
│   └── declab/            # application plumbing shared by all exercises
│       ├── client.py      # POST /v1/systemone
│       ├── questions.py   # request rules, confidence formula
│       ├── exercise.py    # command line of every exercise file
│       ├── checks.py      # checker and fake answers
│       └── ui.py          # Rich rendering
├── docs/
│   └── mental-model.md
└── exercises/
    ├── README.md
    ├── exe00-demo/                 # solved example
    ├── exe01-first-question/       # noul
    ├── exe02-choice/               # choice
    ├── exe03-state/                # the state
    ├── exe04-score/                # score
    ├── exe05-confidence/           # probabilities and confidence
    ├── exe06-multiple-decisions/   # several questions, one state
    ├── exe07-decide-vs-act/        # the model decides, the code acts
    ├── exe08-production-line/      # demo: simulated line, two-step diagnosis
    └── solutions/
```

## The key lesson

A decision model and your application do different jobs:

- **The model** reads a state and gives a probability to each answer of a
  question you wrote. It is good at judgments about text that code cannot make.
- **Your code** decides what the model reads, turns probabilities into
  decisions with thresholds it owns, checks facts it can compute exactly, and
  is the only part that acts.

If a rule matters (a limit, a window, a permission), it is code. If a judgment
about text matters, it is a question with explicit options, and its
probabilities tell your code when to ask a person instead.
