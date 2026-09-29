"""EXE03 — solution."""

from typing import Literal

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError

from mcplab.exercise import run

mcp = MCPServer("exe03-rooms")

PROMPT = (
    "Book the Turing room for Tuesday. "
    "If it is already taken, book the Lovelace room for Tuesday instead."
)

Day = Literal["monday", "tuesday", "wednesday", "thursday", "friday"]

# Server state: lives as long as the server process does.
BOOKINGS: dict[str, dict[str, str]] = {
    "turing": {"tuesday": "robotics seminar"},
    "lovelace": {"monday": "thesis defense"},
    "hopper": {},
}


@mcp.tool()
def book_room(room: str, day: Day) -> str:
    """Book a meeting room for a whole day.

    Fails if the room does not exist or is already booked that day.

    Args:
        room: Room name: 'turing', 'lovelace' or 'hopper'.
        day: Weekday to book.
    """
    key = room.strip().lower()
    if key not in BOOKINGS:
        raise ToolError(f"Unknown room: {room}. Rooms: {', '.join(BOOKINGS)}")
    if day in BOOKINGS[key]:
        free = [name for name, days in BOOKINGS.items() if day not in days]
        raise ToolError(
            f"Room {key} is already booked on {day}. Free rooms on {day}: {', '.join(free)}"
        )
    BOOKINGS[key][day] = "booked by assistant"
    return f"Room {key} booked for {day}"


if __name__ == "__main__":
    run(mcp, PROMPT, __file__)
