from mcplab.checks import error_text, result_value, run_checks


async def checks(client, check):
    tools = (await client.list_tools()).tools
    if not (check.tool(tools, "find_student") and check.tool(tools, "student_courses")):
        return

    result = await client.call_tool("find_student", {"full_name": "Giulia  neri"})
    student_id = result_value(result)
    check.ok(
        student_id == "VR-48213",
        "find_student('Giulia  neri') == 'VR-48213' (case and spaces ignored)",
        student_id,
    )

    result = await client.call_tool("student_courses", {"student_id": "VR-48213"})
    courses = result_value(result)
    check.ok(
        isinstance(courses, list)
        and [course.get("room") for course in courses] == ["Aula Delta", "Aula Gamma"],
        "student_courses('VR-48213') returns her courses with their rooms",
        courses,
    )
    check.ok(
        isinstance(courses, list)
        and all({"code", "title", "room"} <= set(course) for course in courses),
        "each course has code, title and room",
        courses,
    )

    result = await client.call_tool("student_courses", {"student_id": "12345"})
    check.ok(
        result.is_error and "find_student" in error_text(result),
        "a guessed ID fails with an error that points the model to find_student",
        error_text(result),
    )

    result = await client.call_tool("find_student", {"full_name": "Nobody Here"})
    check.ok(
        result.is_error and "nobody" in error_text(result).lower(),
        "an unknown student is a clear error",
        error_text(result),
    )


run_checks(checks, __file__.replace("check.py", "exe04.py"))
