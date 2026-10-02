"""The application around the decision model. It sees the line only through
its logs, its list of machines, and ``repair()``.

- ``symptoms``   — code detects that something is wrong (no model)
- ``trend``      — code turns a series of readings into words (no model)
- ``state``      — how logs become the state the model reads
- ``questions``  — the questions: which machine, which fault
- ``policy``     — thresholds: when to act, when to try the next machine, when to call a person
- ``strategy``   — how the questions are asked: two steps, or one flat question
- ``supervisor`` — symptom -> strategy -> action on the line
- ``report``     — what really happened, after the run
- ``view``       — Rich rendering
"""
