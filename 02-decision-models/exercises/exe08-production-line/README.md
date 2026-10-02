# EXE08 — A production line with a decision-model supervisor

This one is a **demo**: everything is already written. Read it, run it, and
compare the runs. It puts together what EXE01–EXE07 showed one at a time:

- **state**: the logs become what the model reads, and how they are written
  decides whether the model can answer;
- **question types**: a `choice` to pick a machine, then a `choice` over that
  machine's own faults;
- **probabilities**: thresholds decide when to repair, when to try another
  machine, and when to call a person;
- **multiple decisions**: two narrow questions in sequence, instead of one
  broad question;
- **deciding vs acting**: code detects the problem, the model judges its
  cause, code applies the repair, and the simulation shows whether it worked.

## The line

```text
F1 feeder ──> C1 conveyor ──> M1 mill ──> Q1 inspection (camera + gauge)
```

A small simulator in `line/` runs the line one simulated second at a time.
Every machine logs one line per part, with its telemetry. A recipe
([recipes.py](recipes.py)) says how many parts to make and what breaks when:

```python
DEFAULT = Recipe(
    parts=80,
    faults=[
        FaultAt("0820", "C1", "jam"),            # slows the line down
        FaultAt("0850", "M1", "wrong_offset"),   # bad parts, seen downstream at Q1
        FaultAt("0910", "Q1", "gauge_drift"),    # looks like bad parts, but the parts are fine
    ],
)
```

The logs **never name the fault**. They show effects, mixed with normal noise:

```text
0851 C1 TRANSIT part=P-034 cycle_s=124 motor_a=9.1
0851 M1 CUT part=P-034 cycle_s=50 spindle_load=61 temp_c=36.4 probe_mm=40.126
0852 Q1 INSPECT part=P-034 cycle_s=20 image_score=0.94 ref_mm=25.0 dim_mm=40.128 result=REJECT
```

And the faults of one machine look alike: a jam and a slipping belt both slow
the conveyor down; a worn tool, a wrong offset and low coolant all move the
mill's dimensions. Telling them apart needs a judgment about the signals.

| Machine | Faults | What tells them apart |
|---|---|---|
| F1 feeder | `misfeed`, `empty_hopper` | both delay parts; `retries` vs `hopper_kg` |
| C1 conveyor | `jam`, `belt_slip` | both slow transit; motor current up vs down |
| M1 mill | `tool_wear`, `wrong_offset`, `coolant_low` | slow drift with spindle load, a step after a tool change, or rising temperature |
| Q1 inspection | `dirty_lens`, `gauge_drift` | low image score with good dimensions, or the reference block itself reading wrong |

## The supervisor

```text
every minute    symptoms.py    CODE:   too many rejects? too few parts?      no model
                    │
on a symptom        ▼
                state.py       CODE:   logs of the last 10 minutes -> state
                    │
                questions.py   MODEL:  step 1: which machine?   (choice over the machines)
                    │          MODEL:  step 2: which fault?     (choice over that machine's faults + none)
                    ▼
                policy.py      CODE:   p >= 0.60 -> repair; "none" -> next machine; else call a person
                    │
                supervisor.py  CODE:   machine.repair(fault)  -> the simulation goes on
```

The model only appears in the middle. Detecting the problem is counting
(code). Applying the repair is code. If the repair is wrong, the real fault is
still there, the symptom comes back, and the report shows it.

Two ideas from the questions make the two steps work:

- the **router** (step 1) picks among machines, described by their own
  `description`; it never needs to know their faults;
- each **machine** brings its own question (step 2): its fault catalog, with
  the descriptions written next to the fault classes, plus `none`. When the
  model says `none`, the router was probably wrong, and the policy tries the
  next machine.

## Run it

Check the simulator and the supervisor without any model:

```bash
uv run python exercises/exe08-production-line/check.py
```

It verifies that every fault moves some signal out of its nominal range, that
**no state ever contains the name of a fault**, that every remedy removes its
fault, and what the supervisor does with fake answers (repair, try the next
machine, call a person).

Then the demo, about one minute per run on CPU:

```bash
uv run python exercises/exe08-production-line/exe08.py              # two steps, summary state
uv run python exercises/exe08-production-line/exe08.py --verbose    # and every state the model reads
```

At the end, a report compares what the supervisor did with what was really
broken (the simulator knows; the model never sees it).

## Experiments

Change one thing at a time and compare the reports. On one run on CPU with
`tev1:4b-q4_K_M`:

| Command | Right repairs | Technician called | Model calls | Line done at |
|---|---|---|---|---|
| (default) `--strategy two-step --state summary` | 3 of 3 | 0 | 6 | 09:36 |
| `--state raw` | 0 of 3 | 3 | 9 | 10:26 |
| `--strategy flat` | 0 of 3 | 3 | 3 | 10:26 |

**`--state raw`**: the model reads the log lines as they are. It has to find
the step in `probe_mm` among the numbers, and compare each value with a range
it does not know. It cannot: it answers `none` or spreads the probability.
`Summary` (in `state.py`, with `trend.py`) does the part code can do exactly:
it says, for each signal, *stable / rising / step up at 0850* and
*within / above nominal*. It never says why. The model only judges which fault
explains that combination.

**`--strategy flat`**: one question over all ten faults of the line, with the
whole line in the state. The options are many, the state is long, and the
probability spreads: the jam gets 0.52, under the threshold. Two narrow
questions beat one broad question.

In every run, no repair was wrong. When the model is not sure, the policy
calls a technician: slower (the line stops for 20 minutes), but safe. That is
the job of the thresholds in `policy.py`.

More to try:

- `--recipe quiet`: nothing breaks. Does the supervisor stay silent?
- Change `Policy(min_fault_p=...)` in `exe08.py`. With `0.6`, `gauge_drift`
  passes with 0.62. With `0.7`?
- `--model tev1:0.8b` (run `ollama stop tev1:4b-q4_K_M` first, so only one
  model is in memory).
- Move the faults in `recipes.py`, or put two of them at the same time.
- Ollama caches repeated requests: a second identical run is much faster and
  says nothing about cost. Change the recipe's `seed` to get new requests.

## The code

```text
exe08-production-line/
├── exe08.py            # the layout, the detectors, the switches; builds and runs everything
├── recipes.py          # what to produce, what breaks
├── check.py            # the checks, without any model
├── line/               # THE SIMULATION: knows nothing about decision models
│   ├── part.py         # Part: id, dimension, status
│   ├── signal.py       # Signal: a telemetry value and its nominal range
│   ├── logbook.py      # LogLine, LogBook, military time
│   ├── fault.py        # Fault: base class of a fault
│   ├── machine.py      # Machine: base class of a machine (input, output, cycle, faults, logging)
│   ├── machines/       # one machine and its faults per file
│   │   ├── feeder.py
│   │   ├── conveyor.py
│   │   ├── mill.py
│   │   └── inspection.py
│   ├── recipe.py       # Recipe, FaultAt
│   └── line.py         # Line: the clock that moves parts from machine to machine
└── supervisor/         # THE APPLICATION around the model
    ├── symptoms.py     # detectors: code finds that something is wrong
    ├── trend.py        # code turns a series of readings into words
    ├── snapshot.py     # what the supervisor may look at: machines + logs in a window
    ├── state.py        # StateBuilder, RawWindow, Summary
    ├── questions.py    # which machine, which fault, which fault anywhere
    ├── policy.py       # thresholds
    ├── actions.py      # Repair, CallPerson
    ├── strategy.py     # Strategy, TwoStep, Flat: ask the model, return an action
    ├── supervisor.py   # symptom -> strategy -> action on the line
    ├── report.py       # what really happened
    └── view.py         # Rich rendering
```

`line/` never imports `supervisor/`. The supervisor sees the line only through
its logs, its machines (their descriptions and fault catalogs), and
`repair()`.

Read in this order: `line/fault.py`, `line/machine.py`, one machine
(`line/machines/conveyor.py` is the smallest), `supervisor/questions.py`,
`supervisor/strategy.py`, `supervisor/policy.py`, `supervisor/state.py`.

## Write your own machine

The base class does the cycle, the logging, the faults and the repairs. A new
machine declares data, and its faults declare their effects:

```python
# line/machines/washer.py
from ..fault import Fault
from ..machine import Machine
from ..signal import Signal


class CloggedNozzle(Fault):
    description = "A spray nozzle is clogged: pump pressure rises and parts come out dirty."
    remedy = "clean the spray nozzles"

    def affect(self, machine, readings, part):
        readings["pressure_bar"] = round(machine.rng.gauss(6.5, 0.2), 1)


class Washer(Machine):
    kind = "washer"
    description = "Washes the chips off each part after milling."
    cycle_s = 30
    event = "WASH"
    signals = {"pressure_bar": Signal(3.5, 4.5), "water_c": Signal(45, 55)}
    faults = [CloggedNozzle]
```

Export it in `line/machines/__init__.py` and add `("W1", Washer)` to `LAYOUT`
in `exe08.py`, between `M1` and `Q1`. Nothing else changes: the router gets a
new option from `description`, step 2 gets a new question from `faults`,
`Summary` describes the new signals, and `check.py` tests the new fault.

## Think about it

- Where is the line between code and model in `Summary`? Could code also
  decide the fault, with rules on the trends? What would you lose when a new
  fault appears?
- The router reads the summary of every machine. Is it already doing the
  diagnosis? What would happen with 20 machines and the 2,000-token context?
- `WrongOffset` logs an ordinary `TOOL_CHANGE`, like the routine ones every 25
  parts. Why does the model still need the dimensions to tell them apart?
- The policy never repairs below 0.6. What does a wrong repair cost here, and
  what does calling a technician cost? Where would you put the threshold on a
  real line?
- `check.py` tests the supervisor's rules with fake answers. Which parts of
  this application can you test without a model, and which only with one?
