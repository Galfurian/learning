from pathlib import Path

from mcplab.checks import error_text, result_value, run_checks

HERE = Path(__file__).parent


def register_everything(module) -> None:
    """exe07.py simulates and registers in __main__; the check wants all of it."""
    toolbox = module.toolbox
    toolbox.load(module.RECIPE)
    toolbox.register(module.mcp, list(toolbox.TOOLS), list(toolbox.RESOURCES), list(toolbox.PROMPTS))


async def checks(client, check):
    import toolbox

    factory = toolbox.factory
    truth = factory.truth()
    latest = factory.recipe.productions[-1].id

    tools = (await client.list_tools()).tools
    if not all([check.tool(tools, name) for name in ["describe_cell", "get_log", "read_log_page"]]):
        return

    cell = result_value(await client.call_tool("describe_cell", {}))
    check.ok([s["id"] for s in cell["stations"]] == list(factory.stations),
             "describe_cell lists every station of the recipe")
    check.ok([p["id"] for p in cell["productions"]] == [p.id for p in factory.recipe.productions],
             "describe_cell lists every production of the recipe")

    production = next(p for p in cell["productions"] if p["id"] == latest)
    for station, total in production["log_pages"].items():
        text = []
        for page in range(1, total + 1):
            args = {"production": latest, "station": station, "page": page}
            text += result_value(await client.call_tool("read_log_page", args))["lines"].splitlines()
        check.ok(text == factory.logbook.text(station, latest),
                 f"all {total} page(s) of {station} in {latest} give back its whole log")

    result = await client.call_tool("read_log_page", {"production": latest, "station": "WH1", "page": 99})
    check.ok(result.is_error and "pages 1 to" in error_text(result),
             "a page out of range tells the model which pages exist", error_text(result))

    window = {"production": latest, "station": "M1", "start": production["start"], "end": production["end"]}
    expected = [line.text() for line in factory.logbook.lines("M1", latest)]
    collected, start = [], window["start"]
    while True:
        chunk = result_value(await client.call_tool("get_log", {**window, "start": start}))
        check.ok(chunk["line_count"] <= 150, f"get_log from {start} returns at most 150 lines",
                 chunk["line_count"])
        collected += chunk["lines"].splitlines()
        if not chunk["truncated"]:
            break
        start = chunk["next_start"]
    check.ok(collected == expected,
             "following next_start gives back the whole M1 log, without gaps or repeats",
             f"{len(collected)} lines vs {len(expected)}")

    result = await client.call_tool("get_log", {**window, "start": "1000", "end": "0900"})
    check.ok(result.is_error, "a reversed range is an error", error_text(result))
    result = await client.call_tool("get_log", {**window, "start": "9:00"})
    check.ok(result.is_error, "a time not in HHMM format is rejected by the schema", error_text(result))

    check.ok(list(truth.rejected_by_production) == [latest],
             f"only {latest} has rejected parts", truth.rejected_by_production)
    check.ok(len(truth.causes) == 1 and set(truth.causes[0].parts) == set(truth.rejected),
             "every rejected part has one injected fault as its cause", truth.causes)
    gauge = [line for line in factory.logbook.lines("WH1", latest) if line.event == "GAUGE"]
    first_reject = next(line.part for line in gauge if line.fields["result"] == "REJECT")
    check.ok(first_reject == truth.first_rejected,
             f"the warehouse log agrees with the truth: first reject {truth.first_rejected}", first_reject)


    await check_toolkit(client, check, factory, latest)


async def check_toolkit(client, check, factory, latest):
    truth = factory.truth()
    rejected = truth.rejected_by_production[latest]

    summary = result_value(await client.call_tool("production_summary", {"production": latest}))
    check.ok(summary["rejected_at_final_gauge"] == rejected,
             "production_summary lists the parts rejected by the final gauge", summary)

    history = result_value(await client.call_tool("part_history", {"part": rejected[0]}))
    check.ok("WH1 GAUGE" in history["lines"] and "M1 CUT_DONE" in history["lines"],
             f"part_history({rejected[0]}) follows the part from the mill to the gauge")

    text = result_value(await client.call_tool("describe", {"topic": "cell"}))
    check.ok(f"{latest}" in text and "(latest)" in text, "describe('cell') marks the latest production")
    text = result_value(await client.call_tool("describe", {"topic": "GAUGE"}))
    check.ok("FINISHED" in text, "describe('GAUGE') explains the event", text)
    result = await client.call_tool("describe", {"topic": "NOPE"})
    check.ok(result.is_error, "an unknown topic is an error that lists valid topics", error_text(result))

    found = result_value(await client.call_tool(
        "query", {"production": latest, "event": "GAUGE", "contains": "reject"}))
    check.ok(found["matched"] == len(rejected), "query finds the gauge rejects, case-insensitive", found)
    found = result_value(await client.call_tool("query", {"part": rejected[0], "limit": 5}))
    check.ok(found["shown"] == 5 and found["truncated"] and found["lines"].startswith(latest),
             "query respects limit and prefixes lines with the production when searching all")

    counted = result_value(await client.call_tool(
        "count", {"group_by": "result", "production": latest, "event": "GAUGE"}))
    check.ok(counted["counts"].get("REJECT") == len(rejected), "count groups gauges by result", counted)
    counted = result_value(await client.call_tool(
        "count", {"group_by": "production", "event": "GAUGE", "contains": "REJECT"}))
    check.ok(list(counted["counts"]) == [latest], "count by production: only the latest has rejects", counted)

    found = result_value(await client.call_tool(
        "query", {"production": latest, "station": "M1", "contains": "LOAD"}))
    check.ok(all(" M1 LOAD " in line for line in found["lines"].splitlines()),
             "contains matches whole words: LOAD finds no UNLOAD nor load_pct", found["matched"])
    found = result_value(await client.call_tool("query", {"production": latest, "station": "M1"}))
    check.ok(found["truncated"] and "Narrow" in (found["hint"] or ""),
             "a truncated query tells the model how to narrow it", found["hint"])

    import toolbox
    invented = "`0816 M1 TOOL_CHANGE_DONE length_offset_mm=10.2`"
    first_gauge = next(line.text() for line in factory.logbook.lines("WH1", latest)
                       if line.part == truth.first_rejected and line.event == "GAUGE")
    check.ok(toolbox.verify_answer(invented) is not None and "10.2" in toolbox.verify_answer(invented),
             "the host check rejects an answer quoting an invented line")
    check.ok(toolbox.verify_answer(f"Proof: `{first_gauge}`") is None,
             "the host check accepts an answer quoting real lines")
    check.ok(toolbox.verify_answer("It was the mill.") is not None,
             "the host check rejects an answer without quotes")

    found = result_value(await client.call_tool(
        "query", {"production": latest, "station": "M1", "event": "GAUGE"}))
    check.ok(found["matched"] == 0 and "logged by WH1" in (found["hint"] or ""),
             "an empty query says which station really logs the event", found["hint"])

    tool_change = next(line.text() for line in factory.logbook.lines("M1", latest)
                       if line.event == "TOOL_CHANGE_DONE" and line.fields.get("offset_source") == "manual")
    good = (
        f"## Summary\nWrong length offset typed in manually on M1.\n"
        f"## Symptom\n{truth.rejected[0]} to {truth.rejected[-1]} rejected.\n"
        f"## Root cause\nM1 mounted a tool with a manual, wrong length offset.\n"
        f"## Evidence\n```\n{tool_change}\n{first_gauge}\n```\n"
        f"## Ruled out\nThe C1 jam came later.\n## Open questions\nNone\n"
    )
    verdicts = [verdict for _, verdict, _ in toolbox.grade_report(good)]
    check.ok(verdicts == ["✓"] * 6, "the grader gives full marks to a correct report", verdicts)
    wrong = good.replace("Wrong length offset typed in manually on M1.", "The logging system failed.")
    wrong = wrong.replace("M1 mounted a tool with a manual, wrong length offset.", "The gauge did not log.")
    verdicts = dict((aspect, verdict) for aspect, verdict, _ in toolbox.grade_report(wrong))
    check.ok(verdicts["Root cause"] == "✗" and verdicts["Summary"] == "✗",
             "the grader fails a report with the wrong cause", verdicts)

    real = factory.logbook.text("M1", latest)[5]
    quotes = result_value(await client.call_tool(
        "check_quotes", {"lines": [f"**{real}**", "1200 WH1 GAUGE part=P-9999 result=OK"]}))
    check.ok(len(quotes["found"]) == 1 and len(quotes["missing"]) == 1,
             "check_quotes tells real log lines from invented ones", quotes)

    resources = [str(r.uri) for r in (await client.list_resources()).resources]
    check.ok("cell://glossary" in resources, "the glossary is exposed as a resource", resources)
    prompt = await client.get_prompt("investigate_rejects", {"production": latest})
    check.ok(latest in prompt.messages[0].content.text, "prompts/get fills the procedure with the production")


run_checks(checks, str(HERE / "exe07.py"), prepare=register_everything)
