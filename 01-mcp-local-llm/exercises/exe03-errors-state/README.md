# EXE03 — Errors and server state

**MCP concept:** a failed tool call is not a crash. The server returns a result
with `isError: true` and a text message, and the host passes that message to
the model. The model can then react. Also, the server is a long-running
process, so it can keep state between calls.

## Task

In `exe03.py`, write a tool `book_room(room, day)` that books a room in
`BOOKINGS`.

- `room`: string, case-insensitive.
- `day`: one of `monday`, `tuesday`, `wednesday`, `thursday`, `friday`. Invalid
  days must be rejected by the schema, not by your code.
- On success: record the booking in `BOOKINGS` and return a short confirmation.
- If the room does not exist or is already booked that day: fail with a
  message that tells the model what went wrong. A good message also says what
  to do next (for example, which rooms are free that day).

## Step 1: the wrong way

First fail with `raise ValueError("...")`. Run the check and the model:

```bash
uv run python exercises/exe03-errors-state/check.py
uv run python exercises/exe03-errors-state/exe03.py --verbose
```

Look at the error text the model receives. Your message is not there.

## Step 2: the right way

The SDK treats a generic exception as an internal bug and hides its message.
To send a message to the client on purpose, raise `ToolError`:

```python
from mcp.server.mcpserver.exceptions import ToolError
```

Run the check and the model again. Now the model sees why Turing failed and
books Lovelace.

## Think about it

- Why is hiding the text of unexpected exceptions a good default for a server?
- Run the exercise twice. Is Lovelace still free the second time? Why?
  (Hint: who starts and stops the server process?)
- Improve the error message and compare how the model behaves. Error messages
  are part of the prompt.
