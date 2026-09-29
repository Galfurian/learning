"""EXE01 — your first MCP tool. Task: see README.md in this folder."""

from mcp.server import MCPServer

from mcplab.exercise import run

mcp = MCPServer("exe01-letters")

PROMPT = (
    "How many times does the letter 'o' appear in the word "
    "'pneumonoultramicroscopicsilicovolcanoconiosis'?"
)


# TODO: write `count_letter(word, letter)` and register it as an MCP tool.


if __name__ == "__main__":
    run(mcp, PROMPT, __file__)
