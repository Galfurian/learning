"""The simulator's HTTP API: catalog, worker lifecycle, playback position.

Plain JSON over HTTP, no client library. The address comes from ICE_SIM_URL;
the repository holds none. A worker is a test fixture: requested, used and
decommissioned in the same `with` block, also when something fails.
The token stays in memory.
"""

import json
import os
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

Transport = Callable[[str, str, dict[str, Any] | None, str | None], dict[str, Any]]


class SimError(RuntimeError):
    """The simulator refused the request or could not be reached."""


def sim_url() -> str:
    url = os.environ.get("ICE_SIM_URL", "").strip().rstrip("/")
    if not url:
        raise SimError("ICE_SIM_URL is not set: export ICE_SIM_URL=http://<host>:<port> (the simulator's API)")
    return url if url.startswith(("http://", "https://")) else "http://" + url


def http_transport(method: str, path: str, body: dict[str, Any] | None, token: str | None) -> dict[str, Any]:
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode() if body is not None else None
    try:
        with urlopen(Request(sim_url() + path, data=data, headers=headers, method=method), timeout=60) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except HTTPError as exc:
        try:
            detail = json.load(exc).get("detail")
        except (json.JSONDecodeError, AttributeError):
            detail = str(exc)
        raise SimError(f"{method} {path}: HTTP {exc.code}: {detail}") from None
    except URLError as exc:
        raise SimError(f"cannot reach the simulator ({exc.reason}); is the tailnet up?") from None


@dataclass
class Worker:
    id: str
    endpoints: dict[str, str]         # real machine name -> opc.tcp endpoint
    trace: dict[str, Any]
    _token: str = field(repr=False)
    _call: Transport = field(repr=False)

    def play(self) -> dict[str, Any]:
        return self._call("POST", f"/v1/workers/{self.id}/play", None, self._token)

    def pause(self) -> dict[str, Any]:
        return self._call("POST", f"/v1/workers/{self.id}/pause", None, self._token)

    def seek(self, t: float) -> dict[str, Any]:
        return self._call("POST", f"/v1/workers/{self.id}/seek", {"t": t}, self._token)

    def playback(self) -> dict[str, Any]:
        """State, position_s, cycle, speed. Also renews the worker's idle timeout."""
        return self._call("GET", f"/v1/workers/{self.id}", None, self._token)["playback"]

    def decommission(self) -> None:
        self._call("DELETE", f"/v1/workers/{self.id}", None, self._token)


class Sim:
    def __init__(self, transport: Transport = http_transport) -> None:
        self.call = transport

    def traces(self) -> list[dict[str, Any]]:
        data = self.call("GET", "/v1/traces", None, None)
        return data if isinstance(data, list) else data.get("items", [])

    def nodes(self, machine: str, *, trace: str, with_data: bool = True, page: int = 500) -> list[dict[str, Any]]:
        """All nodes of one server, page by page (the API caps the page size)."""
        out, offset = [], 0
        while True:
            q = (f"/v1/machines/{machine}/nodes?trace={trace}&with_data={'true' if with_data else 'false'}"
                 f"&limit={page}&offset={offset}")
            items = self.call("GET", q, None, None)["items"]
            out += items
            if len(items) < page:
                return out
            offset += page

    def worker(self, trace: str, *, speed: float = 1.0) -> "WorkerContext":
        return WorkerContext(self, trace, speed)


class WorkerContext:
    """with sim.worker(trace) as w: ... — the worker is decommissioned on every exit path."""

    def __init__(self, sim: Sim, trace: str, speed: float) -> None:
        self.sim, self.trace, self.speed = sim, trace, speed
        self.worker: Worker | None = None
        self._stop = threading.Event()

    def __enter__(self) -> Worker:
        data = self.sim.call("POST", "/v1/request", {"trace": self.trace, "speed": self.speed, "loop": False}, None)
        token = data.pop("token")
        self.worker = Worker(data["id"], {m["name"]: m["endpoint"] for m in data["machines"]}, data["trace"],
                             token, self.sim.call)
        try:
            self.sim.call("POST", f"/v1/workers/{self.worker.id}/serve", {"autostart": False}, token)
        except Exception:
            self.worker.decommission()
            raise
        threading.Thread(target=self._heartbeat, daemon=True).start()
        return self.worker

    def _heartbeat(self) -> None:
        while not self._stop.wait(300):   # the idle timeout is 30 min; renew every 5
            try:
                self.worker.playback()
            except SimError:
                return

    def __exit__(self, *exc: object) -> None:
        self._stop.set()
        if self.worker is not None:
            self.worker.decommission()
