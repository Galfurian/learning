import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from mcp import Client, MCPError
from mcp.client.stdio import StdioServerParameters
from ollama import AsyncClient, Message

from .bridge import to_ollama_tool, tool_message_from_result
from .model_io import render_model_input
from .ui import (
    show_attached_resource,
    show_context_summary,
    show_context_usage,
    show_discovered_tools,
    show_answer_check,
    live_turn,
    show_final_answer,
    show_grade,
    show_thinking,
    show_user_message,
    show_skipped_call,
    show_mcp_server,
    show_missing_resource,
    show_mcp_prompt,
    show_model_input,
    show_ollama_request,
    show_ollama_response,
    show_resource_catalog,
    show_resource_request,
    show_resource_result,
    show_run_summary,
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


@dataclass
class RunClock:
    """Wall-clock time of one run, split between the model and the tools."""

    started: float
    model_s: float = 0.0
    tools_s: float = 0.0
    steps: int = 0
    tool_calls: int = 0

    @property
    def total_s(self) -> float:
        return time.perf_counter() - self.started


def seconds(nanoseconds: int | None) -> float:
    return (nanoseconds or 0) / 1e9


async def stream_chat(ollama: AsyncClient, view: Any, **request: Any) -> Any:
    """Call Ollama with stream=True, feed the view, and rebuild the whole reply.

    Returns the final chunk (it carries token counts and durations) with
    ``message`` replaced by the complete assistant message.
    """
    thinking, content, tool_calls = "", "", []
    final = None
    async for chunk in await ollama.chat(stream=True, **request):
        delta = chunk.message
        view.add(delta.thinking, delta.content)
        thinking += delta.thinking or ""
        content += delta.content or ""
        tool_calls += delta.tool_calls or []
        final = chunk
    assert final is not None
    final.message = Message(
        role="assistant",
        content=content,
        thinking=thinking or None,
        tool_calls=tool_calls or None,
    )
    return final


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
    system_prompt: str = SYSTEM_PROMPT,
    model: str = DEFAULT_MODEL,
    verbose: bool = False,
    show_raw: bool = False,
    attach: Sequence[str] = (),
    on_demand_resources: bool = False,
    think: bool = False,
    num_ctx: int | None = None,
    mcp_prompt: tuple[str, dict[str, str]] | None = None,
    verify: Callable[[str], str | None] | None = None,
    max_rejections: int = 2,
    one_call_per_step: bool = False,
    show_thinking_text: bool = False,
    grade: Callable[[str], list[tuple[str, str, str]]] | None = None,
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
    ``mcp_prompt`` is ``(name, arguments)`` of an MCP prompt: the host fetches it
    with ``prompts/get`` and uses its messages instead of ``prompt``.
    ``num_ctx`` sets the context window in tokens (Ollama's default otherwise).
    ``verify`` checks each final answer: it returns ``None`` to accept it, or a
    message the host sends back to the model instead of ending the run (at most
    ``max_rejections`` times).
    ``one_call_per_step`` executes only the first tool call of each step and
    answers the others with "not executed", so the model sees one result before
    deciding the next call.
    ``grade`` scores the final answer for the person running the demo; the model
    never sees it. It returns rows of (aspect, verdict, note).
    ``show_thinking_text`` keeps the whole thinking on screen after each call,
    instead of one collapsed line (chat view only).
    Ollama silently drops what does not fit, so every step reports its size.
    """
    clock = RunClock(started=time.perf_counter())
    # Chat view: the default when neither --verbose nor --show-raw is on.
    chat = not verbose and not show_raw
    show_mcp_server(verbose, server_label, model)

    ollama = AsyncClient()
    options = {"num_ctx": num_ctx} if num_ctx else None
    previous_prompt_tokens = 0
    rejections = 0

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

        system = system_prompt
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

        user_messages: list[dict[str, str]] = [{"role": "user", "content": prompt}]
        if mcp_prompt is not None:
            name, arguments = mcp_prompt
            fetched = await mcp.get_prompt(name, arguments)
            user_messages = [
                {"role": message.role, "content": getattr(message.content, "text", "")}
                for message in fetched.messages
            ]
            show_mcp_prompt(verbose, name, arguments, user_messages)
        elif chat:
            show_user_message(prompt)

        messages: list[Any] = [{"role": "system", "content": system}, *user_messages]

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

            model_started = time.perf_counter()
            with live_turn(chat) as view:
                response = await stream_chat(
                    ollama, view, model=model, messages=messages, tools=ollama_tools,
                    think=think, options=options,
                )
            model_s = time.perf_counter() - model_started
            if chat:
                show_thinking(view, full=show_thinking_text)
            clock.model_s += model_s
            clock.steps += 1

            prompt_tokens = response.prompt_eval_count or 0
            # History only grows, so a smaller prompt means Ollama cut it.
            truncated = prompt_tokens < previous_prompt_tokens or (
                num_ctx is not None and prompt_tokens >= num_ctx - 64
            )
            previous_prompt_tokens = max(previous_prompt_tokens, prompt_tokens)
            show_ollama_response(verbose, response.message)
            if not show_raw:
                show_context_usage(
                    step,
                    prompt_tokens,
                    response.eval_count or 0,
                    num_ctx,
                    truncated,
                    len(response.message.thinking or ""),
                    model_s,
                    seconds(response.prompt_eval_duration),
                    seconds(response.eval_duration),
                    clock.total_s,
                )
            messages.append(response.message)

            calls = response.message.tool_calls or []
            if not calls and verify is not None:
                feedback = verify(response.message.content or "")
                retry = feedback is not None and rejections < max_rejections
                show_answer_check(step, feedback, response.message.content or "", retry)
                if retry:
                    rejections += 1
                    messages.append({"role": "user", "content": feedback})
                    continue
            if not calls:
                show_final_answer(response.message.content)
                if grade is not None:
                    show_grade(grade(response.message.content or ""))
                if tracks_resources and not show_raw:
                    show_context_summary(exposed, templates, loaded)
                show_run_summary(
                    clock.total_s,
                    clock.model_s,
                    clock.tools_s,
                    clock.steps,
                    clock.tool_calls,
                )
                return

            for index, call in enumerate(calls):
                name = call.function.name
                arguments = dict(call.function.arguments)

                if one_call_per_step and index > 0:
                    show_skipped_call(verbose, step, name, arguments, quiet=show_raw)
                    messages.append(
                        {
                            "role": "tool",
                            "tool_name": name,
                            "content": "Not executed: call one tool at a time, and look at "
                            "the previous result before choosing the next call.",
                        }
                    )
                    continue

                if on_demand_resources and name == READ_RESOURCE:
                    uri = str(arguments.get("uri", ""))
                    show_resource_request(verbose, step, uri, quiet=show_raw)
                    tool_started = time.perf_counter()
                    try:
                        content = await read_resource_text(mcp, uri)
                        loaded.append(uri)
                    except MCPError as exc:
                        content = f"Error: {exc}"
                    clock.tools_s += time.perf_counter() - tool_started
                    clock.tool_calls += 1
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

                tool_started = time.perf_counter()
                result = await mcp.call_tool(name, arguments)
                tool_s = time.perf_counter() - tool_started
                clock.tools_s += tool_s
                clock.tool_calls += 1
                tool_message, payload = tool_message_from_result(name, result)

                show_tool_result(
                    verbose,
                    step,
                    name,
                    payload,
                    tool_s,
                    arguments=arguments,
                    error=bool(result.is_error),
                    quiet=show_raw,
                )
                messages.append(tool_message)

        show_run_summary(
            clock.total_s, clock.model_s, clock.tools_s, clock.steps, clock.tool_calls
        )
        raise RuntimeError(f"Agent exceeded {max_steps} tool-calling steps")
