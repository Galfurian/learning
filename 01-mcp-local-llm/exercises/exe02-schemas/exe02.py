"""EXE02 — input and output schemas. Task: see README.md in this folder."""

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


# TODO: define a `Train` output model.

# TODO: write `find_trains(...)` and register it as an MCP tool.


if __name__ == "__main__":
    run(mcp, PROMPT, __file__)
