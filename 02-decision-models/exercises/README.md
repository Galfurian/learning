# Exercises

Each exercise is one folder with three files:

```text
exeNN-topic/
├── README.md   # the task, and what concept it teaches
├── exeNN.py    # the file you edit: cases, questions and app code, with a TODO
└── check.py    # verifies your file with fake answers, without any model
```

Start with `exe00-demo`: it is already solved, so you can read a working file
and try every command before writing your own. Then do the others in order.
Each one adds a single concept.

| #  | Folder                                                  | Concept                                                     |
|----|---------------------------------------------------------|-------------------------------------------------------------|
| 00 | [exe00-demo](exe00-demo/)                               | solved example: read, run, trace; nothing to write          |
| 01 | [exe01-first-question](exe01-first-question/)           | a `noul` question; a probability is not a yes/no            |
| 02 | [exe02-choice](exe02-choice/)                           | `choice`: options, descriptions, and a way out (`none`)     |
| 03 | [exe03-state](exe03-state/)                             | the state is all the model reads; it is data, not instructions |
| 04 | [exe04-score](exe04-score/)                             | `score`: ordered levels, the expected value, what it hides  |
| 05 | [exe05-confidence](exe05-confidence/)                   | probabilities, confidence, margin; when a person must decide |
| 06 | [exe06-multiple-decisions](exe06-multiple-decisions/)   | several questions about one state; together vs separately   |
| 07 | [exe07-decide-vs-act](exe07-decide-vs-act/)             | the model decides, the code checks facts, applies rules, acts |

## How one exercise file works

Every `exeNN.py` has the same parts:

```text
CASES                  application data: tickets, emails, records
build_state(case)      APP code: application data -> state       (default: the case itself)
QUESTIONS              what the MODEL is asked about each state
act(case, answers)     APP code: answers -> action
run(QUESTIONS, CASES, __file__, build_state=..., act=...)
```

For every case, `run()` calls `build_state`, sends one request to Ollama, and
passes the answers to `act`. The model only takes part in the middle step.

The plumbing is shared code in `src/declab/`. You only write the parts above.

## Commands

Run from the unit folder (`02-decision-models/`):

```bash
uv run python exercises/exe01-first-question/check.py              # verify, no model
uv run python exercises/exe01-first-question/exe01.py --inspect    # the requests, no model
uv run python exercises/exe01-first-question/exe01.py              # the model decides, the app acts
uv run python exercises/exe01-first-question/exe01.py --verbose    # every HTTP request and response
uv run python exercises/exe01-first-question/exe01.py --case 3     # only case 3
uv run python exercises/exe01-first-question/exe01.py --state "..."  # a state of your own
uv run python exercises/exe01-first-question/exe01.py --separately # one request per question
uv run python exercises/exe01-first-question/exe01.py --model tev1:0.8b  # the small model
```

## Solutions

Reference solutions are in [solutions/](solutions/). Try first. To check a
solution, pass its path to the check:

```bash
uv run python exercises/exe01-first-question/check.py exercises/solutions/exe01.py
```

## Extra

When the exercises are clear, try these on your own. There is no scaffold.

1. **Calibration.** Label 30 emails by hand (meeting or not), run the EXE01
   question on all of them, and group the answers by probability (0.0–0.2,
   0.2–0.4, ...). In each group, how many are really meetings? That is how you
   learn whether 0.8 means 80% on **your** data.
2. **Pick the threshold.** With the same labeled data, choose the EXE01
   threshold that minimizes the cost, if a missed meeting costs 5 and a wrong
   calendar entry costs 1.
3. **Small vs big model.** Run every solution with `--model tev1:0.8b` (after
   `ollama stop tev1:4b-q4_K_M`). Where does the small model fail, and would
   your `act()` have caught it?
4. **Decision model as a router.** Combine with unit 01: ask a `choice`
   question first, and call the generative model of unit 01 only for the
   tickets that need a written answer.
5. **No model.** Replace `decide()` with a function that returns fixed answers.
   Your application still runs. What does that tell you about where the
   behavior lives?
