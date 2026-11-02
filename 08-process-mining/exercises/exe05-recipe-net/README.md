# EXE05 — The recipe as a Petri net

**Concept:** the recipe YAML is a **normative model**: it says what must
happen. Compile it into a Petri net and you can replay a log on it (EXE06),
align a trace with it (EXE07) and follow a running order (EXE09). The
dependencies become places; a step with two dependencies is an AND join;
the fail branch is a choice after `check_covers` that loops back.

## Task

Implement `compile_recipe(recipe)`.

```bash
uv run python exercises/exe05-recipe-net/check.py
uv run python exercises/exe05-recipe-net/exe05.py
uv run python exercises/exe05-recipe-net/exe05.py --recipe parts_test
```

## What to look at

Measured: the gadget net has 13 places, 12 transitions (one silent:
`check_covers:pass`) and 26 arcs. Its play-out up to 15 operations has 231
sequences: the parallel loads and the fail loop multiply them.

The log against the nets (`train`, 32 variants):

| recipe | sequences in the net | variants in it | traces |
|--------|----------------------|----------------|--------|
| brick_demo | 1 | 1 | 33 |
| gadget | 231 | 10 | 94 |
| parts_test | 3 | 3 | 55 |
| no recipe | - | 18 | 18 |

The 18 traces that fit no recipe hold the injected skips, extras, swaps and
stuck orders. The discovered nets of EXE04 describe what happened; the
compiled nets say what must happen. Conformance measures the distance.
