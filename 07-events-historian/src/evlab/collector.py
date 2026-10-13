"""The collector: OPC-UA subscriptions -> change records.

One subscription per server, only to the mapped signals. Each notification is
kept with the collector's wall clock; the playback position is polled every
POLL_S seconds. After the run, each notification gets its event time from the
two polls around it: `event_time_lo` and `event_time_hi` are those positions,
`event_time` the linear interpolation. At speed s the bounds are about s x
POLL_S apart: benchmarks run at speed 1.

`SourceTimestamp` is kept as `source_time` only: on the simulator it is the
time the value was written, not the time it happened on the line.
"""

import asyncio
import re
import bisect
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from .mapping import Mapping
from .records import Change, Manifest
from .sim import Worker

COLLECTOR_VERSION = "1"
POLL_S = 0.5


@dataclass
class Notification:
    wall: float
    machine: str
    signal: str
    value: Any
    source_time: str | None
    seq: int


def plain(value: Any) -> Any:
    """OPC-UA values -> JSON values: lists and structures become text (then the mapping hides it)."""
    if isinstance(value, str):
        if re.fullmatch(r"-?\d+", value.strip()):
            return int(value)                       # numbers served as text ("0", "1")
        if value.strip() == "[]" or (value.startswith("[") and "number=" in value):
            return [int(n) for n in re.findall(r"number=(\d+)", value)]   # a message list served as text
        return value
    if value is None or isinstance(value, bool | int | float):
        return value
    if isinstance(value, list) and all(hasattr(v, "number") for v in value):
        return [int(v.number) for v in value]      # alarm and message lists: keep the numbers, not the text
    return str(value)


def place(wall: float, polls: list[tuple[float, float]]) -> tuple[float | None, float | None, float | None]:
    """(event_time, lo, hi) of a notification at `wall`, from (wall, position) polls sorted by wall."""
    walls = [w for w, _ in polls]
    i = bisect.bisect_right(walls, wall)
    if i == 0 or i == len(polls):
        p = polls[0][1] if i == 0 else polls[-1][1]
        return p, p, p
    (w0, p0), (w1, p1) = polls[i - 1], polls[i]
    t = p0 + (p1 - p0) * ((wall - w0) / (w1 - w0) if w1 > w0 else 0.0)
    return t, p0, p1


def to_changes(notes: list[Notification], polls: list[tuple[float, float]], mapping: Mapping,
               trace_id: str, trace_version: str) -> list[Change]:
    """Notifications in arrival order -> Change records. The first value of every signal has old = None."""
    last: dict[str, Any] = {}
    out = []
    for n in sorted(notes, key=lambda n: n.seq):
        value = mapping.logical_value(n.signal, plain(n.value))
        t, lo, hi = place(n.wall, polls)
        out.append(Change(
            change_id=f"c{len(out) + 1}", source="ice-sim", trace_id=trace_id, trace_version=trace_version,
            machine=n.machine, signal=n.signal, old=last.get(n.signal), new=value,
            event_time=t, event_time_lo=lo, event_time_hi=hi, source_time=n.source_time,
            record_time=datetime.fromtimestamp(n.wall, timezone.utc).isoformat().replace("+00:00", "Z"),
            clock_quality="trace-position", arrival_seq=n.seq))
        last[n.signal] = value
    return out


class _Handler:
    def __init__(self, machine: str, signals: dict[str, str], sink: list[Notification]) -> None:
        self.machine, self.signals, self.sink = machine, signals, sink

    def datachange_notification(self, node, val, data) -> None:
        stamp = data.monitored_item.Value.SourceTimestamp
        self.sink.append(Notification(time.time(), self.machine, self.signals[node.nodeid.to_string()], val,
                                      stamp.isoformat() if stamp else None, len(self.sink)))


async def record(worker: Worker, mapping: Mapping, *, max_s: float | None = None,
                 progress: Callable[[float, int], None] | None = None) -> tuple[list[Notification], list[tuple[float, float]]]:
    """Subscribe, play the trace to its end (or max_s of wall time), return notifications and position polls."""
    from asyncua import Client

    notes: list[Notification] = []
    polls: list[tuple[float, float]] = []
    clients = []
    try:
        for machine in mapping.machines():
            endpoint = worker.endpoints.get(mapping.server(machine))
            if endpoint is None:
                continue
            client = Client(endpoint)
            await client.connect()
            clients.append(client)
            signals = {}
            for name, sig in mapping.signals.items():
                if sig.machine == machine:
                    signals[client.get_node(sig.node_id).nodeid.to_string()] = name
            sub = await client.create_subscription(50, _Handler(machine, signals, notes))
            await sub.subscribe_data_change([client.get_node(k) for k in signals])
        await asyncio.sleep(1.0)                      # initial values arrive before the playback starts
        polls.append((time.time(), 0.0))
        worker.play()
        start = time.time()
        while True:
            await asyncio.sleep(POLL_S)
            state = worker.playback()
            polls.append((time.time(), float(state["position_s"])))
            if progress:
                progress(float(state["position_s"]), len(notes))
            if state["state"] in ("ended", "stopped") or (max_s and time.time() - start > max_s):
                break
        await asyncio.sleep(1.0)                      # late notifications of the last moment
        polls.append((time.time(), polls[-1][1]))
    finally:
        for client in clients:
            await client.disconnect()
    return notes, polls


def manifest_for(worker: Worker, mapping: Mapping, speed: float) -> Manifest:
    return Manifest("ice-sim", worker.trace.get("id"), worker.trace.get("version"), mapping.hash(),
                    COLLECTOR_VERSION, speed, "trace-position")
