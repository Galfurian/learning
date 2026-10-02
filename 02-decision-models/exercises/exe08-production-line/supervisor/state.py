"""How logs become the state the model reads. Two builders, same interface.

- ``RawWindow``: the log lines as they are. The model has to read the numbers.
- ``Summary``: code computes what every signal does (``trend.describe``), and
  the model only judges which fault explains it.

Neither ever names a fault.
"""

from collections import Counter

from line import Machine, hhmm

from .snapshot import Snapshot
from .symptoms import Symptom
from .trend import describe

RAW_LINES_PER_MACHINE = 8


def header(machine: Machine, snapshot: Snapshot) -> str:
    return f"{machine.name} ({machine.kind}), {hhmm(snapshot.start)}-{hhmm(snapshot.end)}:"


class StateBuilder:
    def machine(self, snapshot: Snapshot, name: str) -> str:
        """The state for diagnosing one machine."""
        raise NotImplementedError

    def line(self, snapshot: Snapshot, symptom: Symptom) -> str:
        """The state for choosing a machine: the symptom, then every machine."""
        parts = [f"Problem detected: {symptom.text}"]
        parts += [self.machine(snapshot, machine.name) for machine in snapshot.machines]
        return "\n\n".join(parts)


class RawWindow(StateBuilder):
    def machine(self, snapshot, name):
        machine = snapshot.machine(name)
        lines = snapshot.lines(name)[-RAW_LINES_PER_MACHINE:]
        return "\n".join([header(machine, snapshot)] + [line.text() for line in lines])


class Summary(StateBuilder):
    def machine(self, snapshot, name):
        machine = snapshot.machine(name)
        lines = snapshot.lines(name)
        cycles = [line for line in lines if line.event == machine.event]
        others = [line for line in lines if line.event != machine.event]

        sentences = [f"{header(machine, snapshot)} {len(cycles)} parts."]
        times = [hhmm(line.t) for line in cycles]
        for field, signal in machine.telemetry().items():
            values = [line.fields[field] for line in cycles if field in line.fields]
            if values:
                sentences.append(describe(field, signal, values, times))
        results = Counter(line.fields["result"] for line in cycles if "result" in line.fields)
        if results:
            sentences.append("result: " + ", ".join(f"{count} {name}" for name, count in sorted(results.items())))
        for line in others:
            fields = ", ".join(f"{key}={value}" for key, value in line.fields.items())
            sentences.append(f"event {line.event} at {hhmm(line.t)} ({fields})")
        return "\n".join(sentences)
