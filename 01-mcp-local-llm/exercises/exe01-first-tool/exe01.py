"""EXE01 — your first MCP tool. Task: see README.md in this folder."""

from mcp.server import MCPServer

from mcplab.exercise import run

mcp = MCPServer("exe01-letters")

PROMPT = (
    "How many times does the letter 'o' appear in the word "
    "'pneumonoultramicroscopicsilicovolcanoconiosis'?"
)


# TODO: register this function as an MCP tool, add a docstring, implement it.
def count_letter(word: str, letter: str) -> int:
    raise NotImplementedError


if __name__ == "__main__":
    run(mcp, PROMPT, __file__)
