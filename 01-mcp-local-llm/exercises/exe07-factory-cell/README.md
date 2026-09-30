# EXE07 — Factory cell: long logs, many rounds, thinking

This one is a **demo**: everything is already written. Read it, run it, and
compare the runs. It puts together what EXE01–EXE06 showed one at a time, on
a task that a small model cannot solve in one shot.

**What it shows:**

- a real investigation needs **many rounds** of tool calls;
- every tool result stays in the conversation, so the **context window fills
  up**, and Ollama silently drops what does not fit;
- **thinking** helps the model plan what to read and connect facts found in
  different logs.

## The cell

```text
WH1 warehouse ──> R1 robot ──> C1 conveyor ──> QC1 vision ──> M1 mill
      ^                                                          │
      └──────────── R1 robot brings the part back ───────────────┘
                    WH1 gauges it: OK -> stored, REJECT -> reject bay
```

The logs are not hand-written. They come from a small simulator in
`factory/`: every station is a state machine that advances one simulated
second at a time and writes log lines. The recipe
[recipes/default.yaml](recipes/default.yaml) describes the line and its life:
three production orders of 40 parts each, in three shifts: PO-1001 from 0800
to 1200, PO-1002 from 1200 to 1600, PO-1003 from 1600 to 2000.

Each production has its own logs, and times are military, without a date
(`1752` is 17:52). Stations keep their state from one production to the next:
the mill's tool keeps wearing.

A log line looks like this:

```text
1758 M1 TOOL_CHANGE_DONE tool_in=T13 length_offset_mm=112.387 offset_source=manual
```

The recipe injects three faults:

- PO-1001, 0940: the conveyor jams for four minutes;
- PO-1003, 1752: the mill's tool breaks, and the replacement gets a wrong
  length offset, entered by hand;
- PO-1003, 1815: the conveyor jams again, for three minutes.

Only the gauge of PO-1003 rejects parts, and only one fault causes it. The
model has to find the right production, then the right fault.

## The capabilities

Everything the MCP server can offer lives in [toolbox.py](toolbox.py). The
`__main__` block of `exe07.py` lists which capabilities are switched on:
comment and uncomment lines, run again, compare. The host follows the lists:
it attaches the resources and uses the prompt only when they are on.

```python
TOOLS = [
    "describe_cell", "get_log", "read_log_page",   # raw logs (on by default)
    # "production_summary", "part_history",         # task-shaped
    # "describe", "query", "count", "check_quotes", # swiss army knife
]
RESOURCES = [
    # "cell://glossary",
]
PROMPTS = [
    # "investigate_rejects",
]
```

**Raw log tools.** The model reads and scrolls by itself.

- `describe_cell()`: route, stations and the events each one logs, and the
  productions with their hours and how many log pages each station has;
- `get_log(production, station, start, end)`: the lines of one station in one
  production between two military times, at most 150 at a time. If there are
  more, `truncated` is true and `next_start` says where to continue;
- `read_log_page(production, station, page)`: one page of 100 lines.

Each station logs about 1,200 (QC1) to 3,300 (M1) tokens per production; all
the logs together are about 33,600 tokens, twice the 16,384-token window. The
model has to pick the production, then the stations, then the hours.

**Task-shaped tools.** They answer the questions every investigation asks.

- `production_summary(production)`: ids of the parts stored, rejected by the
  final gauge, scrapped by the camera, unfinished;
- `part_history(part)`: every line about one part, from every station.

**Swiss army knife.** Few generic tools that work for any recipe and any fault.

- `describe(topic)`: documentation on demand. `'cell'` (the latest production
  is marked), a station id, or an event name;
- `query(...)`: one search with optional filters: production, station, event,
  part, text, time window, limit. `part=` alone is a part history;
- `count(group_by, ...)`: the same filters, but counts instead of lines. For
  example `group_by='result', event='GAUGE'` gives OK and REJECT totals;
- `check_quotes(lines)`: tells which lines really exist in the logs. The model
  should call it before answering, so it does not quote lines it never read.

**Resource `cell://glossary`** (about 750 tokens). What every event and field
of every station means, written by the station authors in `factory/stations/`.
The host attaches it to the system message. It addresses the most common
mistake: a camera `REJECT` in QC1 (a raw part, scrapped before milling) is not
a gauge `REJECT` in WH1 (a finished part out of tolerance).

**Prompt `investigate_rejects(production)`.** The third MCP primitive, next to
tools and resources: a ready-made request the user picks from a menu. The host
calls `prompts/get` with the latest production and uses the returned message,
a five-step root-cause procedure, instead of the operator's question.

**The prompts.** The user prompt in `__main__` is what an operator would ask,
knowing nothing about the cause: *"Several finished parts of production order
PO-1003 ended up in the reject bay. What went wrong?"*. The system prompt
(`SYSTEM_PROMPT` in `exe07.py`) is general: a troubleshooting method (pin down
the symptom, follow an affected item back, compare with a good one, check that
each suspect explains the affected items and not the good ones) and a report
format, like an issue template: Summary, Symptom, Root cause, Evidence, Ruled
out, Open questions. Nothing in it mentions this cell or this fault.

**Host behavior.** Two switches in the same `__main__` block change how the
host drives the model, not what the server offers:

- `VERIFY_QUOTES`: when the model answers, the host extracts the quoted log
  lines (`HHMM STATION EVENT ...`) and checks them against the logs. If a line
  does not exist, or nothing is quoted, the host does not accept the answer: it
  sends the model a message listing the invented lines and the run goes on (at
  most twice). This is the host acting as a guarantor, instead of trusting the
  model to call `check_quotes`;
- `ONE_CALL_PER_STEP`: small models often fire several tool calls at once,
  before seeing any result, so later calls cannot use earlier findings. With
  this on, the host executes only the first call of each step and answers the
  others with "not executed: call one tool at a time".

**Grading.** `GRADE = True` makes the host score the final report against the
simulator's truth, after the run. The model never sees the score. The report
is split by its sections and each one is checked:

- *Format*: all six sections are there;
- *Symptom*: the rejected parts, and the first one (`P-0404 to P-0408` counts
  as five parts);
- *Root cause*: the right station and the mechanism. Every fault kind declares
  its own keywords next to its code in `factory/stations/`: for
  `tool_offset_error`, "offset" or "manual" name the mechanism, while "break"
  alone only gets half a point;
- *Evidence*: quoted log lines that exist, and at least one that proves the
  cause or the rejects;
- *Ruled out*: the other faults of the same production are discussed;
- *Summary*: consistent with the real cause.

The result is a table with ✓, ~ and ✗ and a score out of 6.

## Run it

Check the tools and the simulation without any LLM:

```bash
uv run python exercises/exe07-factory-cell/check.py
```

Then run the model. Runs are slow on a CPU: minutes each.

```bash
uv run python exercises/exe07-factory-cell/exe07.py --think
uv run python exercises/exe07-factory-cell/exe07.py --think --show-thinking  # read the thinking
uv run python exercises/exe07-factory-cell/exe07.py                     # no thinking
uv run python exercises/exe07-factory-cell/exe07.py --num-ctx 4096      # smaller window
```

A good sequence of experiments, changing one thing at a time in `__main__`:

1. raw tools only (the default);
2. add the glossary resource;
3. add `production_summary` and `part_history`;
4. replace the raw tools with the swiss army knife;
5. add the `investigate_rejects` prompt;
6. turn on `VERIFY_QUOTES`, then `ONE_CALL_PER_STEP`;
   (keep `GRADE = True` all along, and note the score of each run);
7. try a bigger model with `--model`.

For each run, write down: correct or not, steps, peak context, total time.

After each model call the host prints a line like:

```text
[step 4] context: 9,812 prompt + 412 output = 10,224 / 16,384 tokens (62%) · thought 1,530 chars · model 48.2s (prompt 21.0s, output 26.9s) · elapsed 2m 31s
```

`model` is the time of that Ollama call: reading the prompt, then writing the
answer. `elapsed` is the time since the run started. Each tool result shows its
own time, and the run ends with a total, split between model and tools.

Watch the prompt grow step after step: every log chunk the model reads stays
in the history. If it stops growing or shrinks, Ollama dropped the oldest messages,
and the host prints a red warning.

Add `--show-thinking` to read the model's whole thinking at each step, or
`--verbose` for the full protocol trace. A run
stops after 20 model calls (`max_steps=20` at the bottom of `exe07.py`).

## The simulator

```text
factory/
├── factory.py       # Factory: builds the stations, runs each production, moves parts, computes the truth
├── config.py        # the recipe as Pydantic models (validation + YAML writer)
├── part.py          # a part: route, status, and every contribution to its dimension
├── logbook.py       # log lines, as text or JSON
├── station.py       # Station base class and the @station("type") registry
└── stations/        # one module per station type, imported automatically
```

Look at a run without any model:

```bash
cd exercises/exe07-factory-cell
uv run python -m factory run recipes/default.yaml                          # log sizes + the truth
uv run python -m factory run recipes/default.yaml --log M1 --production PO-1003
```

The truth (which parts were rejected, and which fault caused it) is computed
from the parts themselves: each part records who changed its dimension and
why. Nobody wrote the answer by hand.

## Make your own

- **A new recipe:** copy `recipes/default.yaml`, add a production, move the
  faults or change the timings, set `RECIPE` in `exe07.py`, and ask the model
  again. Quote military times (`"0700"`): unquoted, YAML reads `0700` as an
  octal number, and the recipe is refused. Invalid
  recipes fail with a clear error (unknown station, wrong parameter type,
  fault not supported by that station).
- **A new station type:** add a module to `factory/stations/`, decorate the
  class with `@station("oven")`, define its `Params` and its `step(t)` state
  machine, then use `type: oven` in a recipe. Declare in `faults` which fault
  kinds it supports.

## Think about it

- Which logs did the model read, and which did it skip? Did it use
  `get_log` on the hours around the rejects, or scroll with `read_log_page`?
  Was that choice written in its thinking?
- Comment out `get_log` in `exe07.py` and run again. How far does the model get
  before the context is full?
- The PO-1003 jam happens while a rejected part is on the belt. What in the
  logs rules it out as the cause? And what does the PO-1001 jam tell you?
- Switch on `part_history` or `query`. How much context does the
  investigation need now? What does that say about tool design for small
  models?
- Task-shaped tools answer this investigation; the swiss army knife answers
  any question about the logs. Which set would you ship, and why?
- With the prompt on, the user picks the procedure and the production. Is the
  model still investigating, or following instructions?
