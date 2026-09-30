"""Command line shared by every ``exercises/*/exeNN.py`` file.

One exercise file plays two roles:

- ``python exeNN.py --serve`` runs it as an MCP server over stdio;
- ``python exeNN.py`` runs the HOST, which launches the same file with
  ``--serve`` as a child process and lets the local model use its tools.
"""

import argparse
import asyncio
import json
import logging
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters
from mcp.server import MCPServer

from .agent import DEFAULT_MODEL, SYSTEM_PROMPT, run_agent


async def inspect(server: StdioServerParameters) -> None:
    """Print what a host discovers, without any LLM involved."""
    async with Client(server) as client:
        tools = (await client.list_tools()).tools
        resources = (await client.list_resources()).resources
        templates = (await client.list_resource_templates()).resource_templates

        print(f"tools/list -> {len(tools)} tool(s)")
        for tool in tools:
            print(f"\n- {tool.name}")
            print(f"  description: {tool.description}")
            print(f"  input schema: {json.dumps(tool.input_schema)}")
            if tool.output_schema:
                print(f"  output schema: {json.dumps(tool.output_schema)}")

        print(f"\nresources/list -> {len(resources)} resource(s)")
        for resource in resources:
            print(f"- {resource.uri}  {resource.description or ''}")

        print(f"\nresources/templates/list -> {len(templates)} template(s)")
        for template in templates:
            print(f"- {template.uri_template}  {template.description or ''}")


def parse_args(prompt: str, num_ctx: int | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run this exercise: the local model answers PROMPT using your MCP server."
    )
    parser.add_argument(
        "--prompt",
        default=prompt,
        help="Override the exercise prompt.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help="Any Ollama model installed locally that supports tool calling.",
    )
    parser.add_argument(
        "--num-ctx",
        type=int,
        default=num_ctx,
        help="Context window in tokens"
        + (
            f" (default for this file: {num_ctx})."
            if num_ctx
            else " (default: Ollama's)."
        ),
    )
    parser.add_argument(
        "--show-thinking",
        action="store_true",
        help="Keep the model's whole thinking on screen instead of one collapsed line.",
    )
    parser.add_argument(
        "--think",
        action="store_true",
        help="Let the model reason before each answer or tool call (slower).",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--verbose",
        action="store_true",
        help="Show the full HOST / OLLAMA / MCP SERVER trace.",
    )
    mode.add_argument(
        "--show-raw",
        action="store_true",
        help="Show only the rendered prompt the model receives.",
    )
    mode.add_argument(
        "--inspect",
        action="store_true",
        help="List what the server exposes over MCP, without the model.",
    )
    mode.add_argument(
        "--serve",
        action="store_true",
        help="Run as MCP server over stdio (the host does this for you).",
    )
    return parser.parse_args()


def run(
    mcp: MCPServer,
    prompt: str,
    file: str,
    *,
    system_prompt: str = SYSTEM_PROMPT,
    attach: Sequence[str] = (),
    on_demand_resources: bool = False,
    num_ctx: int | None = None,
    mcp_prompt: tuple[str, dict[str, str]] | None = None,
    verify: Callable[[str], str | None] | None = None,
    one_call_per_step: bool = False,
    grade: Callable[[str], list[tuple[str, str, str]]] | None = None,
    max_steps: int = 8,
) -> None:
    """Entry point of an exercise file: ``run(mcp, PROMPT, __file__)``.

    ``attach`` and ``on_demand_resources`` choose how the host brings MCP
    resources into the model's context; see ``mcplab.agent.run_agent``.
    ``num_ctx`` is this file's default context window; ``--num-ctx`` overrides it.
    ``mcp_prompt`` makes the host build the user message from an MCP prompt.
    ``verify`` and ``one_call_per_step`` change how the host drives the model;
    see ``mcplab.agent.run_agent``.
    ``max_steps`` caps the number of model calls in one run.
    """
    args = parse_args(prompt, num_ctx)

    if args.serve:
        mcp.run(transport="stdio")
        return

    # Importing the exercise created an MCPServer, which enables INFO logging.
    # The host only needs its own trace, not every HTTP request to Ollama.
    logging.getLogger("httpx").setLevel(logging.WARNING)

    path = Path(file).resolve()
    server = StdioServerParameters(
        command=sys.executable,
        args=[str(path), "--serve"],
        cwd=path.parent,
    )

    if args.inspect:
        asyncio.run(inspect(server))
        return

    asyncio.run(
        run_agent(
            args.prompt,
            server,
            server_label=path.name,
            system_prompt=system_prompt,
            model=args.model,
            verbose=args.verbose,
            show_raw=args.show_raw,
            attach=attach,
            on_demand_resources=on_demand_resources,
            think=args.think,
            num_ctx=args.num_ctx,
            mcp_prompt=mcp_prompt,
            verify=verify,
            one_call_per_step=one_call_per_step,
            show_thinking_text=args.show_thinking,
            grade=grade,
            max_steps=max_steps,
        )
    )
