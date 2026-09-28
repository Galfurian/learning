import asyncio
import sys
from pathlib import Path

from mcp import Client
from mcp.client.stdio import StdioServerParameters

SRC = Path(__file__).resolve().parent


async def main() -> None:
    params = StdioServerParameters(
        command=sys.executable,
        args=[str(SRC / "server.py")],
        cwd=SRC,
    )

    async with Client(params) as client:
        page = await client.list_tools()
        print(f"Protocol: {client.protocol_version}")
        print("\nTools discovered through MCP:")
        for tool in page.tools:
            print(f"\n- {tool.name}")
            print(f"  description: {tool.description}")
            print(f"  input schema: {tool.input_schema}")

        result = await client.call_tool("project_code", {"project": "atlas"})
        print("\nDirect MCP call project_code(atlas):")
        print(result.model_dump(by_alias=True, mode="json"))


if __name__ == "__main__":
    asyncio.run(main())
