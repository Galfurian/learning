# EXE03 — Extraction: from prose to mentions

**Concept:** the links between devices are only in the prose. One request
per chunk asks `qwen3:1.7b` for `(subject, relation, object)` triples. The
JSON schema in Ollama's `format` field fixes the shape of the answer and,
by default, lists the relations as an enum. The prompt holds the relations
of `data/scenario.json`, one hint, and one invented example.

The model writes mentions as they appear in the text. Resolution (EXE04,
`Linker`) turns them into nodes; a triple whose two ends do not both resolve
is dropped and counted.

## Task

Implement `parse_triples(raw)` in `exe03.py`: the model's raw text in,
valid mentions and invalid items out.

```bash
uv run python exercises/exe03-extraction/check.py
```

## Run, one step at a time

### 1. One chunk

```bash
uv run python exercises/exe03-extraction/exe03.py --chunk 39
```

Chunk `rovers-missions`: "Rover R-1, also called the first rover, serves
bay 5 and moves a board from the warehouse to pallet 7. StartMission
requires the rover to be idle; the Busy flag in the Status folder of R-1
reports that condition. Rover R-2 serves bay 5 too, but it does not serve
bay 3. …"

Measured (`qwen3:1.7b`, 7.8 s on the first run):

| mention                                   | became |
|-------------------------------------------|--------|
| Rover R-1 serves_bay bay 5                | right link |
| Rover R-2 serves_bay bay 5                | right link |
| Rover R-1 moves board                     | right link |
| Rover R-2 moves board                     | **wrong link**: the text does not say it |
| StartMission requires the rover to be idle | dropped: "the rover" is ambiguous |
| Busy flag observed_by Status folder of R-1 | dropped: backwards, and a folder is not a variable |

No mention for "does not serve bay 3": the model respected the negation
here. Gold has 5 links in this chunk; the graph kept 3 of them and 1 wrong.

### 2. All chunks

```bash
uv run python exercises/exe03-extraction/exe03.py
```

Measured on the 50 chunks (123 gold links):

| relation          | precision | recall |
|-------------------|-----------|--------|
| `serves_bay`      | 1.00      | 0.78   |
| `next_step`       | 1.00      | 1.00   |
| `moves`           | 0.90      | 0.56   |
| `stops`           | 0.75      | 0.75   |
| `requires`        | 1.00      | 0.44   |
| `incident_on`     | 1.00      | 0.32   |
| `fixed_by_method` | 1.00      | 0.26   |
| `confirms`        | 0.50      | 0.20   |
| `raised`          | 1.00      | 0.10   |
| `observed_by`     | 0.00      | 0.00   |
| all               | 0.93      | 0.45   |

About 4 s per chunk on a CPU, 3–4 minutes for the corpus, then cached.

- **High precision, low recall:** what the graph keeps is mostly right;
  half of the links never arrive. The last line shows where they go: most
  ends are "not resolved".
- **Simple relations work, chained ones do not:** `serves_bay` and
  `next_step` name two things the text names plainly. `observed_by` needs
  a condition ("the rover to be idle") and a variable ("the Busy flag in
  the Status folder of R-1"): long mentions that rarely resolve.
- **Incidents:** `raised` 0.10. The incident is "the incident" (a hint in
  the prompt), the alarm is a paraphrase ("an RFID reader fault"); one of the
  two ends usually fails.

### 3. Without the enum

```bash
uv run python exercises/exe03-extraction/exe03.py --free
```

The relation is any string. Measured: 10 invalid items ("has", "must
report home", "incidents_on", …), precision 0.95, recall 0.45: the same as
with the enum. The enum removes invalid relation names; it does not make
the model choose the right one.

### 4. A larger model

```bash
uv run python exercises/exe03-extraction/exe03.py --extract-model qwen3:4b
```

Measured: 13.0 s per chunk, precision 0.96, recall 0.40. Three times the
cost, no gain: the losses are in resolution, not in the model's reading.
