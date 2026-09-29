from mcplab.checks import run_checks


async def read_text(client, uri):
    result = await client.read_resource(uri)
    return "".join(getattr(content, "text", "") or "" for content in result.contents)


async def checks(client, check):
    resources = (await client.list_resources()).resources
    uris = [str(resource.uri) for resource in resources]
    check.ok("lab://rules" in uris, "resources/list exposes 'lab://rules'", uris)

    templates = (await client.list_resource_templates()).resource_templates
    patterns = [template.uri_template for template in templates]
    check.ok(
        "lab://machines/{machine}" in patterns,
        "resources/templates/list exposes 'lab://machines/{machine}'",
        patterns,
    )

    tools = (await client.list_tools()).tools
    check.ok(
        not tools,
        "no tools: the model cannot fetch these, only the host can",
        [tool.name for tool in tools],
    )

    if "lab://rules" in uris:
        text = await read_text(client, "lab://rules")
        check.ok("Saturday" in text, "reading 'lab://rules' returns the rules text", text[:80])

    if "lab://machines/{machine}" in patterns:
        text = await read_text(client, "lab://machines/laser-cutter")
        check.ok(
            "never unattended" in text,
            "reading 'lab://machines/laser-cutter' returns its safety notes",
            text,
        )
        text = await read_text(client, "lab://machines/3d-printer")
        check.ok("unattended" in text, "the same template serves 'lab://machines/3d-printer'", text)


run_checks(checks, __file__.replace("check.py", "exe05.py"))
