# EXE04 — Entity resolution

**Concept:** extraction returns **mentions** ("the first rover", "Busy
flag", "low air pressure alarm"); a graph needs **nodes** (`rover1`,
`rover1/Status/Busy`, `alarm:conveyor/NoAirPressure`). Resolution maps one
to the other, and it fails in two ways:

- **split:** a mention resolves to nothing; the fact is lost;
- **merge:** a mention resolves to the wrong node; the fact lands on another
  entity and looks right.

A mention that fits two nodes ("the rover", with two robots) must stay
**ambiguous**: picking one is a merge with a 50% chance of being wrong.

## Task

Implement `normalize(text)` and `resolve(mention, exact, normal)` in
`exe04.py`.

```bash
uv run python exercises/exe04-resolution/check.py
```

## Run

```bash
uv run python exercises/exe04-resolution/exe04.py
```

The run resolves the 349 mentions of `data/mentions.json` (every surface
form the notes use, with its gold node) three ways. Measured with the
reference solution:

| resolver                       | right | wrong (merge) | none (split) | accuracy |
|--------------------------------|-------|---------------|--------------|----------|
| exact only                     | 121   | 2             | 223          | 0.35     |
| yours (exact, then normalized) | 216   | 2             | 128          | 0.62     |
| + type and chunk scope         | 319   | 4             | 23           | 0.92     |

Look at:

- **exact only:** two mentions in three are lost. The prose says "the first
  rover", the node is named "Rover R-1".
- **yours:** normalization and aliases recover about a hundred. The "Not
  right" table shows what is left: "Busy flag", "LastResult", "board" are
  **ambiguous** (every device has a Busy flag; "board" is an item and a
  method parameter).
- **+ type and chunk scope:** the library's `Linker` (src/kglab/builder.py)
  adds two things your resolver does not know: the type the relation
  expects (a `moves` object is an Item, not a Parameter) and the devices the
  chunk names (in a note about the CNC cell, "Busy flag" is the CNC's). The
  split errors drop from 128 to 23; the merges rise from 2 to 4. Context
  resolves more, and sometimes it resolves wrong.
- "the rover" counts as right only when the resolver says ambiguous.

The built graph (EXE00, EXE03) uses the `Linker`.
