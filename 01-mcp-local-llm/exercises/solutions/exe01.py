"""EXE01 — solution."""

from mcp.server import MCPServer

from mcplab.exercise import run

mcp = MCPServer("exe01-letters")

PROMPT = (
    "How many times does the letter 'o' appear in the word "
    "'pneumonoultramicroscopicsilicovolcanoconiosis'?"
)


@mcp.tool()
def count_letter(word: str, letter: str) -> int:
    """Count how many times a letter appears in a word (case-insensitive).

    Args:
        word: The word to inspect, for example 'strawberry'.
        letter: A single letter to look for, for example 'r'.
    """
    return word.lower().count(letter.lower())


if __name__ == "__main__":
    run(mcp, PROMPT, __file__)
