"""EXE04 — chaining tools. Task: see README.md in this folder."""

from mcp.server import MCPServer

from mcplab.exercise import run

mcp = MCPServer("exe04-campus")

PROMPT = "In which rooms are the courses of the student Giulia Neri held?"

STUDENTS = {
    "giulia neri": "VR-48213",
    "marco bianchi": "VR-50977",
}

ENROLLMENTS = {
    "VR-48213": ["EMB-01", "NET-07"],
    "VR-50977": ["NET-07", "ML-03"],
}

COURSES = {
    "EMB-01": {"title": "Embedded Systems", "room": "Aula Delta"},
    "NET-07": {"title": "Computer Networks", "room": "Aula Gamma"},
    "ML-03": {"title": "Machine Learning", "room": "Aula Alfa"},
}


# TODO: write `find_student(full_name)` and register it as an MCP tool.

# TODO: write `student_courses(student_id)` and register it as an MCP tool.


if __name__ == "__main__":
    run(mcp, PROMPT, __file__)
