# Mental model: events and historian

Numbers from `lab-session` (18.7 min of the lab line, replayed at speed
1), 12 dev questions and 7 holdout questions, `qwen3:1.7b` on a CPU.

## 1. A variable is not an event

The nine servers expose 3,872 nodes; 276 of them change in the trace; the
unit maps 81 to logical signals. A change says "this value is now
that". An event says "something happened": a mission started, a check
failed, a pallet arrived. Rules turn the first into the second.

## 2. Time has bounds

The simulator's `SourceTimestamp` is the moment the value was written, not
the moment it happened on the line. The collector polls the playback
position every 0.5 s and places each notification between two polls:

| recording speed | median bound width |
|-----------------|--------------------|
| 1               | 0.52 s             |
| 10              | 5.15 s             |

At speed s the uncertainty is about s × 0.5 s. Durations and orders are
measured at speed 1. Two events whose bounds overlap are not ordered.

## 3. Cleaning

Of 2,258 changes, 81 are initial values (the state at subscription, not an
event). The real recording had no duplicates; the fixture has them on
purpose. A replay restart resets the state.

## 4. Three kinds of claims in one sentence

"The QC check of pallet 7 failed":

- **observed:** the check mission started and ended (one change each);
- **derived:** the check failed (the mission plus the fault counter that
  moved within its window);
- **inferred:** it was pallet 7's check (pallet 7 occupied the QC bay at
  that time; no signal names the pallet).

Of 1,323 events, 227 belong to a case, and 18 of those links are inferred.

## 5. An assignment is an intention

`conveyor.destination.bay4_2 = 7` says where pallet 7 should go. The pallet
went there only if it left the loop while assigned (the segment FIFOs show
it). The chain marks each visit as corroborated or not.

## 6. "Why" comes from a rule

The generator explains only what a causal rule produced: "a failed check,
then the covers taken off and dropped in the bin" is a rework. For pallet 8
no rule explains why it went to the assembly bay; the right answer says the
recording does not show why. The expected route of a product is unit 08.

## 7. What the benchmark says

Three runs of each set, factual rubric:

| set     | questions | right   | first failing stage |
|---------|-----------|---------|---------------------|
| dev     | 12        | 5 to 8  | GENERATION only     |
| holdout | 7         | 3 to 4  | SELECTION 1, GENERATION 2–3 |

Evidence recall was 1.00 on both sets: the pipeline found the evidence. The
losses are in the small generator, and they move from run to run: a
benchmark of a sampling generator needs several runs. One holdout question
named no pallet, and the selector could not reach its case.
