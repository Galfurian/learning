# EXE02 — Choosing one option

**Concept:** a `choice` question lists the options, and the model returns a
probability for **every** one of them. The probabilities always sum to 1 over
the options you listed, so the model cannot say "none of these" unless "none"
is an option. The option keys are what your code branches on; the
descriptions are what the model reads.

## Step 1: options without descriptions, and no way out

`exe02.py` starts with three options and no descriptions. Implement `act()`
first (return the `QUEUES` entry of the chosen option), then run:

```bash
uv run python exercises/exe02-choice/exe02.py
```

Look at case 4 (a broken laptop screen) and case 5 (the canteen menu). Neither
fits any queue, but each one still gets an option. Look at the probabilities
and the confidence of those two cases: they are the only sign of the problem.

## Step 2: the complete question

Complete `criteria` so that the options are exactly the keys of `QUEUES`:
`printer`, `network`, `account`, `hardware`, `none`. Give every option a short
description that says what belongs there, for example
`"printer": "Printers and scanners: paper jams, print quality, toner."`.

Run again. Now case 4 and case 5 have a place to go.

The answer you receive has this shape:

```python
answers = {"queue": {"type": "choice", "choice": "printer",
                     "probabilities": {"printer": 0.97, "network": 0.01, ...},
                     "confidence": 0.88}}
```

## Verify

```bash
uv run python exercises/exe02-choice/check.py
uv run python exercises/exe02-choice/exe02.py --verbose
```

## Think about it

- Remove the `none` option and keep the descriptions. Where does the canteen
  menu go now, and with what probability?
- The keys are for your code, the descriptions are for the model. Rename
  `network` to `n1` and keep its description. Does the answer change?
- Two options overlap (for example "the VPN rejects my password": network or
  account?). What do the probabilities look like? How should the app handle a
  close call? (EXE05 comes back to this.)
- Why is `act()` a dictionary lookup and not an `if` on text? What would go
  wrong if the model could answer with free text?
