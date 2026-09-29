"""EXE03 — errors and server state. Task: see README.md in this folder."""

from mcp.server import MCPServer

from mcplab.exercise import run

mcp = MCPServer("exe03-rooms")

PROMPT = (
    "Book the Turing room for Tuesday. "
    "If it is already taken, book the Lovelace room for Tuesday instead."
)

# Server state: lives as long as the server process does.
BOOKINGS: dict[str, dict[str, str]] = {
    "turing": {"tuesday": "robotics seminar"},
    "lovelace": {"monday": "thesis defense"},
    "hopper": {},
}


# TODO: write `book_room(room, day)` and register it as an MCP tool.


if __name__ == "__main__":
    run(mcp, PROMPT, __file__)
