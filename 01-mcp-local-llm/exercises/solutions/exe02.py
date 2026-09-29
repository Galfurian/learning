"""EXE02 — solution."""

from typing import Literal

from pydantic import BaseModel

from mcp.server import MCPServer

from mcplab.exercise import run

mcp = MCPServer("exe02-trains")

PROMPT = (
    "I am in Verona and I need to reach Milano on a high-speed train "
    "leaving after 09:00. Which trains can I take?"
)

TIMETABLE = [
    {"number": "RV 2206", "origin": "verona", "destination": "milano", "departs": "07:45", "kind": "regional"},
    {"number": "FR 9711", "origin": "verona", "destination": "milano", "departs": "08:52", "kind": "high-speed"},
    {"number": "RV 2210", "origin": "verona", "destination": "milano", "departs": "09:45", "kind": "regional"},
    {"number": "FR 9715", "origin": "verona", "destination": "milano", "departs": "10:52", "kind": "high-speed"},
    {"number": "IC 8841", "origin": "verona", "destination": "milano", "departs": "12:10", "kind": "high-speed"},
    {"number": "RV 2231", "origin": "verona", "destination": "venezia", "departs": "09:30", "kind": "regional"},
    {"number": "FR 9420", "origin": "verona", "destination": "venezia", "departs": "11:05", "kind": "high-speed"},
    {"number": "RV 2215", "origin": "milano", "destination": "verona", "departs": "10:25", "kind": "regional"},
]


class Train(BaseModel):
    number: str
    departs: str
    kind: Literal["regional", "high-speed"]


@mcp.tool()
def find_trains(
    origin: str,
    destination: str,
    departs_after: str = "00:00",
    kind: Literal["regional", "high-speed", "any"] = "any",
) -> list[Train]:
    """Find direct trains between two cities, ordered by departure time.

    Args:
        origin: Departure city, for example 'verona'.
        destination: Arrival city, for example 'milano'.
        departs_after: Earliest departure time as 24h 'HH:MM'. Defaults to the whole day.
        kind: Kind of train, or 'any' to accept every kind.
    """
    return [
        Train(number=row["number"], departs=row["departs"], kind=row["kind"])
        for row in TIMETABLE
        if row["origin"] == origin.strip().lower()
        and row["destination"] == destination.strip().lower()
        and row["departs"] >= departs_after
        and kind in ("any", row["kind"])
    ]


if __name__ == "__main__":
    run(mcp, PROMPT, __file__)
