from mcplab.checks import error_text, result_value, run_checks

WEEKDAYS = {"monday", "tuesday", "wednesday", "thursday", "friday"}


async def checks(client, check):
    tools = (await client.list_tools()).tools
    tool = check.tool(tools, "book_room")
    if tool is None:
        return

    day = tool.input_schema.get("properties", {}).get("day", {})
    check.ok(
        set(day.get("enum", [])) == WEEKDAYS,
        "'day' is an enum of the five weekdays",
        day,
    )

    async def book(room, day):
        return await client.call_tool("book_room", {"room": room, "day": day})

    result = await book("turing", "tuesday")
    text = error_text(result)
    check.ok(result.is_error, "booking a taken room returns isError=true", result_value(result))
    check.ok(
        "turing" in text.lower() and "tuesday" in text.lower(),
        "the error text explains the problem to the model (ToolError, not ValueError)",
        text,
    )

    result = await book("lovelace", "tuesday")
    check.ok(not result.is_error, "booking a free room succeeds", error_text(result))

    result = await book("Lovelace", "tuesday")
    check.ok(
        result.is_error,
        "the same booking now fails: state persists between calls",
        result_value(result),
    )

    result = await book("babbage", "monday")
    check.ok(
        result.is_error and "babbage" in error_text(result).lower(),
        "an unknown room is a clear error",
        error_text(result),
    )

    result = await book("hopper", "sunday")
    check.ok(
        result.is_error and "day" in error_text(result),
        "day='sunday' is rejected by schema validation, before your code runs",
        error_text(result),
    )


run_checks(checks, __file__.replace("check.py", "exe03.py"))
