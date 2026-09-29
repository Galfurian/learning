from mcplab.checks import result_value, run_checks


async def checks(client, check):
    tools = (await client.list_tools()).tools
    tool = check.tool(tools, "count_letter")
    if tool is None:
        return

    schema = tool.input_schema
    properties = schema.get("properties", {})
    check.ok(tool.description, "the tool has a description (docstring)")
    check.ok(
        properties.get("word", {}).get("type") == "string"
        and properties.get("letter", {}).get("type") == "string",
        "inputSchema declares 'word' and 'letter' as strings",
        properties,
    )
    check.ok(
        set(schema.get("required", [])) == {"word", "letter"},
        "both arguments are required",
        schema.get("required"),
    )

    for word, letter, expected in [
        ("pneumonoultramicroscopicsilicovolcanoconiosis", "o", 9),
        ("strawberry", "r", 3),
        ("Mississippi", "s", 4),
        ("Verona", "V", 1),
        ("banana", "z", 0),
    ]:
        result = await client.call_tool("count_letter", {"word": word, "letter": letter})
        value = result_value(result)
        check.ok(
            not result.is_error and value == expected,
            f"count_letter({word!r}, {letter!r}) == {expected}",
            value,
        )


run_checks(checks, __file__.replace("check.py", "exe01.py"))
