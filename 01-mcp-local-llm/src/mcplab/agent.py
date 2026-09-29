from collections.abc import Sequence
from typing import Any

from mcp import Client, MCPError
from mcp.client.stdio import StdioServerParameters
from ollama import AsyncClient

from .bridge import to_ollama_tool, tool_message_from_result
from .model_io import render_model_input
from .ui import (
    show_attached_resource,
    show_context_summary,
    show_discovered_tools,
    show_final_answer,
    show_mcp_server,
    show_missing_resource,
    show_model_input,
    show_ollama_request,
    show_ollama_response,
    show_resource_catalog,
    show_resource_request,
    show_resource_result,
    show_tool_call,
    show_tool_result,
)

DEFAULT_MODEL = "qwen3:1.7b"

SYSTEM_PROMPT = (
    "You are a small local assistant. Use the available tools whenever "
    "the answer depends on information exposed by them. Do not invent tool results "
    "or tool arguments. Keep calling tools until the user's request is fully done."
)

# A tool that belongs to the HOST, not to the MCP server. When the model calls
# it, the host sends MCP resources/read. It only exists in on-demand mode.
READ_RESOURCE = "read_resource"

READ_RESOURCE_TOOL = {
    "type": "function",
    "function": {
        "name": READ_RESOURCE,
        "description": (
            "Load the full content of one document listed in the system message. "
            "Use it only when the user's request needs that document."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "uri": {
                    "type": "string",
                    "description": "Exact URI of the document, as listed.",
                },
            },
            "required": ["uri"],
        },
    },
}


async def read_resource_text(mcp: Client, uri: str) -> str:
    """Read one MCP resource and keep only its text contents."""
    result = await mcp.read_resource(uri)
    return "\n".join(
        content.text
        for content in result.contents
        if getattr(content, "text", None) is not None
    )


def resource_catalog(resources: list[Any]) -> str:
    """Describe the listed resources without their content."""
    lines = [
        f"- {resource.uri}: {resource.description or resource.name}"
        for resource in resources
    ]
    return (
        "The MCP server exposes these documents. Their content is NOT in this "
        f"conversation. To load one, call {READ_RESOURCE} with its exact URI, "
        "and only if the user's request needs it.\n" + "\n".join(lines)
    )


async def run_agent(
    prompt: str,
    server: StdioServerParameters,
    *,
    server_label: str,
    model: str = DEFAULT_MODEL,
    verbose: bool = False,
    show_raw: bool = False,
    attach: Sequence[str] = (),
    on_demand_resources: bool = False,
    think: bool = False,
    max_steps: int = 8,
) -> None:
    """Answer ``prompt`` with a local model that can use the server's MCP tools.

    Resources can reach the model in two ways:

    - ``attach`` lists URIs the HOST reads up front and places in the system
      message, whether the request needs them or not;
    - ``on_demand_resources`` puts only the resource list (URI + description)
      in the system message, and gives the model a host tool to load one.
      The host sends ``resources/read`` only when the model asks.

    ``think`` lets the model reason before answering or calling tools.
    """
    show_mcp_server(verbose, server_label, model)

    ollama = AsyncClient()

    async with Client(server) as mcp:
        listed = await mcp.list_tools()
        show_discovered_tools(
            verbose,
            listed.tools,
            quiet=show_raw,
        )

        ollama_tools = [to_ollama_tool(tool) for tool in listed.tools]
        tracks_resources = bool(attach) or on_demand_resources
        exposed: list[Any] = []
        templates: list[Any] = []
        loaded: list[str] = []

        if tracks_resources:
            exposed = (await mcp.list_resources()).resources
            templates = (await mcp.list_resource_templates()).resource_templates

        system = SYSTEM_PROMPT
        for uri in attach:
            try:
                text = await read_resource_text(mcp, uri)
            except MCPError as exc:
                show_missing_resource(uri, exc)
                continue
            show_attached_resource(verbose, uri, text, quiet=show_raw)
            system += f"\n\nReference document ({uri}):\n{text}"
            loaded.append(uri)

        if on_demand_resources:
            show_resource_catalog(verbose, exposed, quiet=show_raw)
            system += "\n\n" + resource_catalog(exposed)
            ollama_tools.append(READ_RESOURCE_TOOL)

        messages: list[Any] = [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ]

        for step in range(1, max_steps + 1):
            if show_raw:
                rendered = await render_model_input(
                    model,
                    messages,
                    ollama_tools,
                    think,
                )
                show_model_input(step, rendered)

            show_ollama_request(
                verbose,
                step=step,
                model=model,
                messages=messages,
                tool_count=len(ollama_tools),
            )

            response = await ollama.chat(
                model=model,
                messages=messages,
                tools=ollama_tools,
                think=think,
            )

            show_ollama_response(verbose, response.message)
            messages.append(response.message)

            calls = response.message.tool_calls or []
            if not calls:
                show_final_answer(response.message.content)
                if tracks_resources and not show_raw:
                    show_context_summary(exposed, templates, loaded)
                return

            for call in calls:
                name = call.function.name
                arguments = dict(call.function.arguments)

                if on_demand_resources and name == READ_RESOURCE:
                    uri = str(arguments.get("uri", ""))
                    show_resource_request(verbose, step, uri, quiet=show_raw)
                    try:
                        content = await read_resource_text(mcp, uri)
                        loaded.append(uri)
                    except MCPError as exc:
                        content = f"Error: {exc}"
                    show_resource_result(verbose, step, uri, content, quiet=show_raw)
                    messages.append(
                        {"role": "tool", "tool_name": READ_RESOURCE, "content": content}
                    )
                    continue

                show_tool_call(
                    verbose,
                    step,
                    name,
                    arguments,
                    quiet=show_raw,
                )

                result = await mcp.call_tool(name, arguments)
                tool_message, payload = tool_message_from_result(name, result)

                show_tool_result(
                    verbose,
                    step,
                    name,
                    payload,
                    quiet=show_raw,
                )
                messages.append(tool_message)

        raise RuntimeError(f"Agent exceeded {max_steps} tool-calling steps")
