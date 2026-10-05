"""EXE09 tool mode: the generative model decides when to search, and with which query.

Four runtime actors: the APP (host), the GENERATIVE MODEL, the MCP SERVER
(search_manuals), and, inside the server, the EMBEDDING MODEL.
"""

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from mcp import Client
from mcp.client.stdio import StdioServerParameters

from .client import Tracer, chat
from .generation import REFUSAL, CitationReport, check_citations

TOOL_PROMPT = f"""You answer questions about the machine manuals of one plant.
You cannot see the manuals. Call search_manuals with a short search query to get excerpts. Each excerpt has an id.
You may search again with a different query if the excerpts do not answer the question.
Answer only from the excerpts. After every sentence that uses an excerpt, write its id in square brackets.
If the excerpts do not contain the answer, reply exactly: {REFUSAL}"""


def to_ollama_tool(tool: Any) -> dict[str, Any]:
    return {"type": "function",
            "function": {"name": tool.name, "description": tool.description or "", "parameters": tool.input_schema}}


def excerpts_from(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, dict):
        if "excerpts" in payload:
            return list(payload["excerpts"])
        if isinstance(payload.get("result"), dict):
            return excerpts_from(payload["result"])
        return []
    if isinstance(payload, list):
        for block in payload:
            if isinstance(block, dict) and block.get("type") == "text":
                try:
                    return excerpts_from(json.loads(block["text"]))
                except json.JSONDecodeError:
                    continue
    return []


@dataclass
class ToolRun:
    answer: str
    searches: list[str]
    seen: list[dict[str, Any]]
    citations: CitationReport
    steps: int
    prompt_tokens: int
    seconds: float


async def run_tool_agent(
    question: str,
    server_script: Path,
    *,
    model: str,
    num_ctx: int,
    max_steps: int = 4,
    tracer: Tracer | None = None,
) -> ToolRun:
    server = StdioServerParameters(command=sys.executable, args=[str(server_script)])
    async with Client(server) as mcp:
        tools = [to_ollama_tool(t) for t in (await mcp.list_tools()).tools]
        messages: list[dict[str, Any]] = [{"role": "system", "content": TOOL_PROMPT},
                                          {"role": "user", "content": question}]
        seen: list[dict[str, Any]] = []
        searches: list[str] = []
        answer = f"(no final answer after {max_steps} steps)"
        prompt_tokens, seconds, steps = 0, 0.0, 0
        for steps in range(1, max_steps + 1):
            result = chat(model, messages, num_ctx=num_ctx, tools=tools, tracer=tracer)
            prompt_tokens, seconds = result.prompt_tokens, seconds + result.seconds
            messages.append(result.message)
            if not result.tool_calls:
                answer = result.content
                break
            for call in result.tool_calls:
                name = call["function"]["name"]
                arguments = call["function"].get("arguments") or {}
                searches.append(str(arguments.get("query", arguments)))
                out = await mcp.call_tool(name, arguments)
                payload = (out.structured_content if out.structured_content is not None
                           else [block.model_dump(mode="json") for block in out.content])
                if tracer is not None:
                    tracer("MCP SERVER", f"tools/call {name}", arguments, {"excerpts": excerpts_from(payload)})
                for excerpt in excerpts_from(payload):
                    if excerpt["id"] not in {s["id"] for s in seen}:
                        seen.append(excerpt)
                messages.append({"role": "tool", "tool_name": name, "content": json.dumps(payload, ensure_ascii=False)})
        return ToolRun(answer, searches, seen, check_citations(answer, [s["id"] for s in seen]),
                       steps, prompt_tokens, seconds)
