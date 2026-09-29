from mcplab.checks import error_text, result_value, run_checks


async def checks(client, check):
    tools = (await client.list_tools()).tools
    tool = check.tool(tools, "find_trains")
    if tool is None:
        return

    schema = tool.input_schema
    properties = schema.get("properties", {})
    required = set(schema.get("required", []))

    check.ok(
        required == {"origin", "destination"},
        "only 'origin' and 'destination' are required",
        sorted(required),
    )
    check.ok(
        properties.get("departs_after", {}).get("default") == "00:00",
        "'departs_after' defaults to '00:00'",
        properties.get("departs_after"),
    )
    kind = properties.get("kind", {})
    check.ok(
        set(kind.get("enum", [])) == {"regional", "high-speed", "any"}
        and kind.get("default") == "any",
        "'kind' is an enum regional | high-speed | any, default 'any'",
        kind,
    )
    check.ok(
        tool.output_schema is not None,
        "the tool publishes an outputSchema (structured output)",
    )

    result = await client.call_tool(
        "find_trains",
        {"origin": "Verona", "destination": "Milano", "departs_after": "09:00", "kind": "high-speed"},
    )
    value = result_value(result)
    check.ok(
        not result.is_error and isinstance(value, list),
        "the result is structured content (a list of trains)",
        value,
    )
    if isinstance(value, list):
        check.ok(
            [train.get("number") for train in value] == ["FR 9715", "IC 8841"],
            "Verona -> Milano, high-speed, after 09:00 gives FR 9715 and IC 8841",
            value,
        )
        check.ok(
            all(set(train) == {"number", "departs", "kind"} for train in value),
            "each train has exactly: number, departs, kind",
            value,
        )

    result = await client.call_tool("find_trains", {"origin": "verona", "destination": "venezia"})
    value = result_value(result)
    check.ok(
        isinstance(value, list) and len(value) == 2,
        "defaults apply: all trains Verona -> Venezia",
        value,
    )

    result = await client.call_tool(
        "find_trains", {"origin": "verona", "destination": "milano", "kind": "bus"}
    )
    check.ok(
        result.is_error and "kind" in error_text(result),
        "kind='bus' is rejected by schema validation, before your code runs",
        error_text(result),
    )


run_checks(checks, __file__.replace("check.py", "exe02.py"))
