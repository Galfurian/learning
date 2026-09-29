from mcplab.checks import run_checks

MACHINES = ["laser-cutter", "3d-printer", "oscilloscope", "reflow-oven"]


async def read_text(client, uri):
    result = await client.read_resource(uri)
    return "".join(getattr(content, "text", "") or "" for content in result.contents)


async def checks(client, check):
    resources = {str(resource.uri): resource for resource in (await client.list_resources()).resources}
    expected = [f"lab://manuals/{machine}" for machine in MACHINES]

    check.ok(
        sorted(resources) == sorted(expected),
        "resources/list exposes one static resource per manual",
        sorted(resources),
    )

    tools = (await client.list_tools()).tools
    check.ok(not tools, "no tools: the server only exposes resources", [tool.name for tool in tools])

    for uri in expected:
        resource = resources.get(uri)
        if resource is None:
            continue
        description = resource.description or ""
        check.ok(
            "manual" in description.lower() and len(description) < 200,
            f"{uri} has a short description (what the model sees before loading)",
            description,
        )
        text = await read_text(client, uri)
        check.ok(
            "operating manual" in text and len(text) > len(description),
            f"resources/read {uri} returns the full manual",
            text[:60],
        )


run_checks(checks, __file__.replace("check.py", "exe06.py"))
