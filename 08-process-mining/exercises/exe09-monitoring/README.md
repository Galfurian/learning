# EXE09 — Online monitoring

**Concept:** a running order has a prefix: the entries seen so far. Which
recipes can it still be? A recipe stays a **candidate** while its net
replays the prefix with no deviation. The recipes share their first steps,
so on that prefix the honest answer is "gadget or parts_test, not decided
yet" (`inferred`). The first event that only one recipe can do decides it
(`derived`, with its event id). The deciding activities say what to look
for next.

## Task

Implement `candidates(prefix, nets)`. The replay is given:
`pmlab.monitor.prefix_fit` plays the prefix on one recipe net (a prefix
alignment of cost 0) and says if the recipe still fits;
`continuations` gives what can still follow. You write the filter, the
claim kind, the deciding event and the deciding map.

```bash
uv run python exercises/exe09-monitoring/check.py
uv run python exercises/exe09-monitoring/exe09.py
```

## What to look at

Measured on `ref-order`:

| t (s) | last entry | candidates | claim | deciding |
|-------|------------|------------|-------|----------|
| 0 | - | brick_demo, gadget, parts_test | inferred | load_bricks: brick_demo; load_board, load_covers: gadget/parts_test |
| 230 | reserve_pallet (complete) | gadget, parts_test | inferred | buffer_board, check_covers: gadget; mill_part: parts_test |
| 380 | test_board (complete) | gadget, parts_test | inferred | buffer_board, check_covers: gadget; mill_part: parts_test |
| 380.5 | check_covers (start) | gadget | derived | decided at e17, e18, e19, e29 |
| 1118 | engrave_gadget (start) | gadget | derived | decided at e17, e18, e19, e29 |

The recipe is decided at t=380.5 s, when the covers pallet starts its QC
check. Before that, a person at the line could not tell either.

On `train`, whole traces: 185 of 200 orders decided, all 185 on the true
recipe; 13 fit no recipe (deviations); 2 stay undecided (stuck on the
shared prefix).
