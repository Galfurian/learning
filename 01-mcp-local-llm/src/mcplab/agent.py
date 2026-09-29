from collections.abc import Sequence
from typing import Any

from mcp import Client, MCPError
from mcp.client.stdio import StdioServerParameters
from ollama import AsyncClient

from .bridge import to_ollama_tool, tool_message_from_result
from .model_io import render_model_input
from .ui import (
    show_attached_resource,
    show_discovered_tools,
    show_final_answer,
    show_mcp_server,
    show_missing_resource,
    show_model_input,
    show_ollama_request,
    show_ollama_response,
    show_tool_call,
    show_tool_result,
)

DEFAULT_MODEL = "qwen3:1.7b"

SYSTEM_PROMPT = (
    "You are a small local assistant. Use the available tools whenever "
    "the answer depends on information exposed by them. Do not invent tool results "
    "or tool arguments. Keep calling tools until the user's request is fully done."
)


async def read_resource_text(mcp: Client, uri: str) -> str:
    """Read one MCP resource and keep only its text contents."""
    result = await mcp.read_resource(uri)
    return "\n".join(
        content.text
        for content in result.contents
        if getattr(content, "text", None) is not None
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
    think: bool = False,
    max_steps: int = 8,
) -> None:
    """Answer ``prompt`` with a local model that can use the server's MCP tools.

    ``attach`` lists MCP resource URIs the HOST reads up front and places in
    the system message. Resources are chosen by the host, not by the model.
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

        system = SYSTEM_PROMPT
        for uri in attach:
            try:
                text = await read_resource_text(mcp, uri)
            except MCPError as exc:
                show_missing_resource(uri, exc)
                continue
            show_attached_resource(verbose, uri, text, quiet=show_raw)
            system += f"\n\nReference document ({uri}):\n{text}"

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
                return

            for call in calls:
                name = call.function.name
                arguments = dict(call.function.arguments)

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
