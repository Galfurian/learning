"""EXE07 — a solved demo: long logs, many rounds, thinking. See README.md.

All capabilities live in toolbox.py. The __main__ block below chooses which
ones the MCP server offers: switch them on and off, run again, compare.
"""

from pathlib import Path

from mcp.server import MCPServer

import toolbox
from mcplab.exercise import run

# Point this at your own recipe to investigate a different line.
RECIPE = Path(__file__).parent / "recipes" / "default.yaml"

mcp = MCPServer("exe07-factory-cell")

SYSTEM_PROMPT = """\
You are a troubleshooting assistant. You investigate problems using only the
data you can get through your tools.

How to investigate:
1. Understand the system first: what its components are and what its data means.
2. Pin down the symptom: what exactly is wrong, which items are affected, where,
   and since when.
3. Follow one affected item back through the system, step by step.
4. Compare it with an item that was fine. The cause is among the differences.
5. For each suspect, check that the affected items show it and the good items
   do not. Something that only happened at the same time is not a cause.
6. Stop when one cause explains all the affected items and none of the good ones.

Rules:
- Call one tool, read its result, then decide the next call.
- Every statement must come from a tool result. Quote data exactly as the tools
  returned it. Never quote something you have not read.
- If a result is truncated or empty, refine the request instead of guessing.

When you are done, answer with this report, and nothing else:

## Summary
One sentence: what went wrong.

## Symptom
What was observed, where and when. Which items are affected: the first one and
how many in total.

## Root cause
The cause, and how it produced the symptom.

## Evidence
The exact lines returned by the tools that prove the root cause, one per line,
in a code block.

## Ruled out
Other suspects you checked, and why each one is not the cause.

## Open questions
What is still uncertain, or "None".
"""


if __name__ == "__main__":
    TOOLS = [
        # Raw logs: the model reads and scrolls by itself.
        "describe_cell",
        "get_log",
        "read_log_page",
        # Task-shaped: answers to the questions an investigation always asks.
        "production_summary",
        "part_history",
        # Swiss army knife: few generic tools, combined with filters.
        "describe",
        "query",
        "count",
        "check_quotes",
    ]
    # Resources the host reads up front and puts in the system message.
    RESOURCES = [
        "cell://glossary",
    ]
    # An MCP prompt the host uses instead of PROMPT: a ready-made procedure.
    PROMPTS = [
        # "investigate_rejects",
    ]

    # How the host drives the model.
    # Check every final answer: quoted log lines must exist, or the answer goes back.
    VERIFY_QUOTES = False
    # Execute only the first tool call of each step: one result before the next choice.
    ONE_CALL_PER_STEP = False
    # Score the final report against the simulator's truth (shown to you, not to the model).
    GRADE = True

    toolbox.register(mcp, TOOLS, RESOURCES, PROMPTS)

    # The logs come from simulating the line, not from a hand-written file.
    factory = toolbox.load(RECIPE)
    # Get the ID of the latest production order, to investigate it in the prompt.
    latest = factory.recipe.productions[-1].id
    # The user's question, asked the way an operator would: what they saw, nothing more.
    prompt = (
        f"Several finished parts of production order {latest} ended up in the reject bay. "
        "What went wrong?"
    )
    # The system prompt: a general troubleshooting method and a report format.
    # Nothing in it is specific to this cell or to this fault.
    system_prompt = SYSTEM_PROMPT

    run(
        mcp,
        prompt,
        __file__,
        system_prompt=SYSTEM_PROMPT,
        # attach=RESOURCES,
        verify=toolbox.verify_answer if VERIFY_QUOTES else None,
        one_call_per_step=ONE_CALL_PER_STEP,
        grade=toolbox.grade_report if GRADE else None,
        num_ctx=16384,
        max_steps=20,
    )
