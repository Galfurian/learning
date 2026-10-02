"""The simulated production line. It knows nothing about decision models.

- ``part``      — a part and its dimension
- ``signal``    — a telemetry signal with its nominal range
- ``logbook``   — log lines, and the clock format they use
- ``fault``     — base class of a fault
- ``machine``   — base class of a machine: input, output, work cycle, logging
- ``machines/`` — the concrete machines, one per file
- ``recipe``    — what to produce and what to break
- ``line``      — the clock that moves parts from machine to machine
"""

from .fault import Fault
from .line import Line
from .logbook import LogBook, LogLine, hhmm
from .machine import Machine
from .part import Part
from .recipe import FaultAt, Recipe
from .signal import Signal

__all__ = ["Fault", "FaultAt", "Line", "LogBook", "LogLine", "Machine", "Part", "Recipe", "Signal", "hhmm"]
