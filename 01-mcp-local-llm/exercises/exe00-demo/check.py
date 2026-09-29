from mcplab.checks import error_text, result_value, run_checks


async def checks(client, check):
    # MCP tools/list: what a host discovers.
    tools = (await client.list_tools()).tools
    if not (check.tool(tools, "inventory_count") and check.tool(tools, "project_code")):
        return

    # MCP tools/call: invoke a tool by name, no LLM involved.
    result = await client.call_tool("project_code", {"project": "atlas"})
    check.ok(result_value(result) == "A7-KAPPA", "project_code('atlas') == 'A7-KAPPA'", result_value(result))

    result = await client.call_tool("inventory_count", {"part": "Servo-X12"})
    check.ok(result_value(result) == 17, "inventory_count('Servo-X12') == 17", result_value(result))

    result = await client.call_tool("project_code", {"project": "zeus"})
    check.ok(
        result.is_error and "zeus" in error_text(result),
        "an unknown project returns isError=true with a readable message",
        error_text(result),
    )


run_checks(checks, __file__.replace("check.py", "exe00.py"))
